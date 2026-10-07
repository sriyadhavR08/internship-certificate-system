import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from unittest import skipUnless
from unittest.mock import patch
from django.test import override_settings, TransactionTestCase
from django.db import connection, close_old_connections
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from accounts.models import User, StudentProfile
from internships.models import Internship
from certificates.models import Certificate, CertificateSequence
from certificates.content import paragraphs
from certificates.services import generate

PAYLOAD = dict(full_name='Kaviya', email='kaviya@example.test', gender='FEMALE', mobile_number='9876543210',
               college_name='Test College', department='Computer Science', course='BSc', register_number='REG001',
               project_name='Zentime', start_date='2026-09-01', end_date='2026-09-30',
               password='Test!Pass987#', confirm_password='Test!Pass987#')


class WorkflowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.media = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media, REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
            'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
            'DEFAULT_THROTTLE_CLASSES': [],
            'EXCEPTION_HANDLER': 'accounts.api_errors.exception_handler',
        })
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(shutil.rmtree, self.media, True)
        self.admin = User.objects.create_superuser('admin@example.test', 'Admin!987#', full_name='Administrator')
        response = self.client.post('/api/auth/register/', PAYLOAD)
        self.assertEqual(response.status_code, 201, response.data)
        self.student = User.objects.get(email=PAYLOAD['email'])
        self.internship = self.student.internship

    def admin_login(self):
        self.client.force_authenticate(self.admin)

    def complete(self):
        self.admin_login()
        for status in ['IN_PROGRESS', 'COMPLETED']:
            result = self.client.patch(f'/api/admin/internships/{self.internship.pk}/status/', {'status':status})
            self.assertEqual(result.status_code, 200, result.data)

    def issue(self):
        self.complete()
        result = self.client.post(f'/api/admin/certificates/generate/{self.internship.pk}/')
        self.assertEqual(result.status_code, 201, result.data)
        return Certificate.objects.get(pk=result.data['id'])

    def test_registration_defaults_and_password(self):
        self.assertEqual(self.student.role, 'STUDENT')
        self.assertTrue(self.student.check_password(PAYLOAD['password']))
        self.assertNotEqual(self.student.password, PAYLOAD['password'])
        self.assertEqual(self.internship.status, 'REGISTERED')
        self.assertFalse(Certificate.objects.exists())

    def test_duplicate_email_case_insensitive(self):
        response = self.client.post('/api/auth/register/', {**PAYLOAD, 'email':'KAVIYA@example.test','register_number':'REG002'})
        self.assertEqual(response.status_code,400)

    def test_duplicate_register_number_case_insensitive(self):
        response = self.client.post('/api/auth/register/', {**PAYLOAD, 'email':'other@example.test','register_number':'reg001'})
        self.assertEqual(response.status_code,400)

    def test_registration_cannot_escalate_role_or_issue(self):
        response = self.client.post('/api/auth/register/', {**PAYLOAD, 'email':'other@example.test','register_number':'REG002','role':'ADMIN','status':'CERTIFICATE_ISSUED','is_staff':True})
        self.assertEqual(response.status_code,201)
        user = User.objects.get(email='other@example.test')
        self.assertFalse(user.is_staff)
        self.assertEqual(user.role,'STUDENT')
        self.assertEqual(user.internship.status,'REGISTERED')

    def test_invalid_dates_password_and_mobile(self):
        for extra in [{'end_date':'2026-09-01'},{'end_date':'2026-12-31'},{'end_date':'2026-09-05'},{'confirm_password':'no'},{'mobile_number':'abc'}]:
            response = self.client.post('/api/auth/register/', {**PAYLOAD,'email':'other@example.test','register_number':'REG002',**extra})
            self.assertEqual(response.status_code,400)

    def test_login_and_refresh_and_logout(self):
        result=self.client.post('/api/auth/login/',{'email':'KAVIYA@example.test','password':PAYLOAD['password']})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.data['user']['role'],'STUDENT')
        tokens=result.data
        self.client.credentials(HTTP_AUTHORIZATION='Bearer '+tokens['access'])
        self.assertEqual(self.client.get('/api/student/profile/').status_code,200)
        fresh=self.client.post('/api/auth/token/refresh/',{'refresh':tokens['refresh']})
        self.assertEqual(fresh.status_code,200)
        self.assertEqual(self.client.post('/api/auth/token/refresh/',{'refresh':tokens['refresh']}).status_code,401)
        self.assertEqual(self.client.post('/api/auth/logout/',{'refresh':fresh.data['refresh']}).status_code,200)
        self.assertEqual(self.client.post('/api/auth/token/refresh/',{'refresh':fresh.data['refresh']}).status_code,401)

    def test_student_rejected_from_all_admin_operations(self):
        self.assertEqual(self.client.get('/api/admin/students/').status_code,401)
        self.client.force_authenticate(self.student)
        for method,path,payload in [('get','/api/admin/students/',{}),('put',f'/api/admin/students/{self.student.pk}/',PAYLOAD),('patch',f'/api/admin/internships/{self.internship.pk}/status/',{'status':'COMPLETED'}),('get',f'/api/admin/certificates/preview/{self.internship.pk}/',{}),('post',f'/api/admin/certificates/generate/{self.internship.pk}/',{}),('patch','/api/admin/certificates/1/revoke/',{})]:
            self.assertEqual(getattr(self.client,method)(path,payload).status_code,403)

    def test_status_sequence_and_future_completion(self):
        self.admin_login()
        url=f'/api/admin/internships/{self.internship.pk}/status/'
        self.assertEqual(self.client.patch(url,{'status':'COMPLETED'}).status_code,400)
        self.assertEqual(self.client.patch(url,{'status':'IN_PROGRESS'}).status_code,200)
        self.internship.end_date=date(2099,1,1);self.internship.save()
        self.assertEqual(self.client.patch(url,{'status':'COMPLETED'}).status_code,400)

    def test_generate_before_completion_rejected(self):
        self.admin_login()
        self.assertEqual(self.client.post(f'/api/admin/certificates/generate/{self.internship.pk}/').status_code,400)
        self.assertFalse(Certificate.objects.exists())

    def test_admin_corrections_and_preview_no_side_effects(self):
        self.admin_login()
        result=self.client.put(f'/api/admin/students/{self.student.pk}/',{**PAYLOAD,'full_name':'Kaviya R'})
        self.assertEqual(result.status_code,200,result.data)
        preview=self.client.get(f'/api/admin/certificates/preview/{self.internship.pk}/')
        self.assertEqual(preview.status_code,200)
        self.assertTrue(preview.content.startswith(b'%PDF'))
        self.assertFalse(Certificate.objects.exists())
        self.assertFalse(CertificateSequence.objects.exists())

    def test_generation_download_duplicate_and_immutable(self):
        cert=self.issue()
        self.assertRegex(cert.certificate_id,r'^INT-\d{4}-\d{5}$')
        self.assertEqual(len(cert.verification_token),43)
        self.assertTrue(cert.pdf_file.storage.exists(cert.pdf_file.name))
        self.internship.refresh_from_db()
        self.assertEqual(self.internship.status,'CERTIFICATE_ISSUED')
        self.assertEqual(self.client.post(f'/api/admin/certificates/generate/{self.internship.pk}/').status_code,400)
        self.assertEqual(self.client.put(f'/api/admin/students/{self.student.pk}/',PAYLOAD).status_code,400)
        self.client.force_authenticate(self.student)
        result=self.client.get(f'/api/certificates/{cert.pk}/download/')
        self.assertEqual(result.status_code,200)
        self.assertTrue(b''.join(result.streaming_content).startswith(b'%PDF'))
        self.assertEqual(result['Cache-Control'],'no-store')

    def test_ownership_and_no_public_media(self):
        cert=self.issue()
        stranger=User.objects.create_user('stranger@example.test','Strong987!')
        self.client.force_authenticate(stranger)
        self.assertEqual(self.client.get(f'/api/certificates/{cert.pk}/download/').status_code,403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(f'/api/certificates/{cert.pk}/download/').status_code,401)
        self.assertEqual(self.client.get('/media/'+cert.pdf_file.name).status_code,404)

    def test_verification_token_id_and_privacy(self):
        cert=self.issue()
        self.client.force_authenticate(None)
        by_token=self.client.get(f'/api/public/verify/token/{cert.verification_token}/')
        by_id=self.client.get(f'/api/public/verify/id/{cert.certificate_id}/')
        self.assertEqual(by_token.data,by_id.data)
        self.assertEqual(set(by_token.data),{'student_name','project_name','start_date','end_date','certificate_id','issue_date','status'})
        self.assertEqual(by_token.data['status'],'VALID')
        self.assertEqual(self.client.get('/api/public/verify/id/INT-0000-00000/').status_code,404)

    def test_revoke_and_download_denial(self):
        cert=self.issue()
        self.assertEqual(self.client.patch(f'/api/admin/certificates/{cert.pk}/revoke/').status_code,200)
        self.assertEqual(self.client.patch(f'/api/admin/certificates/{cert.pk}/revoke/').status_code,200)
        result=self.client.get(f'/api/public/verify/token/{cert.verification_token}/')
        self.assertEqual(result.data['status'],'REVOKED')
        self.assertEqual(set(result.data),{'student_name','certificate_id','status'})
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get(f'/api/certificates/{cert.pk}/download/').status_code,403)

    def test_pronouns_and_escaping(self):
        data={'student_name':'Kaviya <R>', 'project_name':'Zentime & Co', 'start_date':'2026-09-01','end_date':'2026-09-30','gender':'FEMALE'}
        female=' '.join(paragraphs(data))
        self.assertIn('Ms. Kaviya &lt;R&gt;',female)
        self.assertIn('her internship',female)
        self.assertIn('she undertakes',female)
        self.assertIn('Zentime &amp; Co',female)
        male=' '.join(paragraphs({**data,'gender':'MALE','student_name':'Arun'}))
        self.assertIn('Mr. Arun',male)
        self.assertIn('his internship',male)
        self.assertIn('making him',male)
        self.assertIn('he undertakes',male)
        self.assertNotIn('Mohana',female)
        self.assertNotIn('Virtue Hire',female)

    def test_pdf_failure_rolls_back_issue(self):
        self.complete()
        with patch('certificates.services.render_pdf',side_effect=RuntimeError('test failure')):
            with self.assertRaises(RuntimeError):generate(self.internship.pk)
        self.assertFalse(Certificate.objects.exists())
        self.assertFalse(CertificateSequence.objects.exists())
        self.internship.refresh_from_db()
        self.assertEqual(self.internship.status,'COMPLETED')

    def test_final_issuance_revalidates_corrected_dates(self):
        self.complete()
        self.internship.end_date=date(2099,1,1)
        self.internship.save(update_fields=['end_date'])
        self.assertEqual(self.client.post(f'/api/admin/certificates/generate/{self.internship.pk}/').status_code,400)
        self.assertFalse(Certificate.objects.exists())

    def test_invalid_logout_token_is_not_server_error(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.post('/api/auth/logout/',{'refresh':'invalid'}).status_code,401)

    def test_admin_search_and_filters(self):
        self.admin_login()
        self.assertEqual(self.client.get('/api/admin/students/?search=Kaviya&status=REGISTERED').data['count'],1)
        self.assertEqual(self.client.get('/api/admin/students/?project_name=missing').data['count'],0)
        self.assertEqual(self.client.get('/api/admin/students/?start_date=invalid').status_code,400)


@skipUnless(connection.vendor=='mysql','Row locking is tested against MySQL only.')
class ConcurrentIssuanceTests(TransactionTestCase):
    def setUp(self):
        self.media=tempfile.mkdtemp()
        self.override=override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(shutil.rmtree,self.media,True)
        user=User.objects.create_user('parallel@example.test','Parallel!123',full_name='Parallel Test')
        StudentProfile.objects.create(user=user,gender='MALE',mobile_number='9876543210',college_name='College',department='CS',course='BSc',register_number='PAR1')
        self.internship=Internship.objects.create(student=user,project_name='Concurrency',start_date='2026-09-01',end_date='2026-09-30',status='COMPLETED')

    def test_simultaneous_issuance_only_one_record(self):
        def issue():
            close_old_connections()
            try:
                return generate(self.internship.pk).certificate_id
            except Exception as exc:
                return str(exc)
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:issue(),range(2)))
        self.assertEqual(Certificate.objects.count(),1,results)
        self.assertEqual(sum(x.startswith('INT-') for x in results),1,results)
        self.assertTrue(any('already been generated' in x for x in results),results)
