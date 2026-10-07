param(
    [string]$DataDirectory = (Join-Path $PSScriptRoot '../../../work/mysql-data'),
    [string]$MySqlBase = 'C:\Program Files\MySQL\MySQL Server 8.0'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $DataDirectory)) {
    throw 'The workspace MySQL data directory was not found. Use the normal MySQL setup in README.md, or supply -DataDirectory.'
}
$DataDirectory = (Resolve-Path -LiteralPath $DataDirectory).Path
$probe = [System.Net.Sockets.TcpClient]::new()
try {
    $probe.Connect('127.0.0.1', 3307)
    Write-Host 'Port 3307 is already listening. The backend will validate the configured database credentials.'
    return
} catch {
    # Start only when this development port is not listening.
} finally {
    $probe.Dispose()
}
$server = Join-Path $MySqlBase 'bin/mysqld.exe'
if (-not (Test-Path -LiteralPath $server)) { throw "MySQL server executable not found: $server" }
$logDirectory = Split-Path -Parent $DataDirectory
$arguments = @('--no-defaults', "--basedir=`"$MySqlBase`"", "--datadir=`"$DataDirectory`"", '--port=3307', '--bind-address=127.0.0.1', '--mysqlx=OFF', '--console')
$process = Start-Process -FilePath $server -ArgumentList $arguments -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'mysql-console.log') -RedirectStandardError (Join-Path $logDirectory 'mysql-errors.log') -PassThru
Write-Host "Started local MySQL process $($process.Id) on 127.0.0.1:3307. Logs: $logDirectory"
