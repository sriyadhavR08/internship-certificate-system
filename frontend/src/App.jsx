import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/Auth";
import { Loading } from "./components/Common";
import Shell from "./layouts/Shell";
import Home from "./pages/public/Home";
import { Login, Register } from "./pages/public/AuthPages";
import Verify from "./pages/public/Verify";
import StudentDashboard from "./pages/student/Dashboard";
import AdminDashboard from "./pages/admin/Dashboard";
import Students from "./pages/admin/Students";
import StudentDetail from "./pages/admin/StudentDetail";
import Certificates from "./pages/admin/Certificates";
function Protected({ role }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role)
    return (
      <Navigate
        to={user.role === "ADMIN" ? "/admin/dashboard" : "/student/dashboard"}
        replace
      />
    );
  return <Outlet />;
}
function PublicOnly() {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;
  return user ? (
    <Navigate
      to={user.role === "ADMIN" ? "/admin/dashboard" : "/student/dashboard"}
      replace
    />
  ) : (
    <Outlet />
  );
}
export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Home />} />
        <Route element={<PublicOnly />}>
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
        </Route>
        <Route path="verify" element={<Verify />} />
        <Route path="verify/:token" element={<Verify />} />
        <Route element={<Protected role="STUDENT" />}>
          <Route path="student/dashboard" element={<StudentDashboard />} />
        </Route>
        <Route element={<Protected role="ADMIN" />}>
          <Route path="admin/dashboard" element={<AdminDashboard />} />
          <Route path="admin/students" element={<Students />} />
          <Route path="admin/internships" element={<Students />} />
          <Route path="admin/students/:id" element={<StudentDetail />} />
          <Route path="admin/certificates" element={<Certificates />} />
        </Route>
        <Route
          path="*"
          element={
            <div className="text-center py-5">
              <h1>Page not found</h1>
              <a href="/">Return home</a>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
