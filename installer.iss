; =====================================================
; Sistema Cobros Don Atilio - Instalador FINAL
; Seed integrado en main.py (no necesita archivo separado)
; =====================================================

#define MyAppName "Sistema Cobros Don Atilio"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "Don Atilio Supermercado"
#define MyAppExeName "SistemaCobrosDonAtilio.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Instalador_Output
OutputBaseFilename=InstaladorDonAtilio_v{#MyAppVersion}_FINAL
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; --- App (CON ICONO EMBEBIDO + SEED INTEGRADO) ---
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; --- LOGO PARA ACCESOS DIRECTOS ---
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

; --- SQL de estructura ---
Source: "app\database\schema.sql"; DestDir: "{app}"; Flags: ignoreversion

; --- Variables de entorno ---
#ifexist "installer_scripts\.env.production"
Source: "installer_scripts\.env.production"; DestDir: "{app}"; DestName: ".env"; Flags: ignoreversion
#else
#error Falta el archivo installer_scripts\.env.production
#endif

; --- Script que instala/levanta MariaDB/MySQL embebido ---
Source: "installer_scripts\setup_mysql.bat"; DestDir: "{app}"; Flags: ignoreversion

; --- MySQL/MariaDB portable (tu carpeta mysql...) ---
Source: "mysql\*"; DestDir: "{app}\mysql"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- Script de reparación opcional ---
Source: "reparar_mysql.bat"; DestDir: "{app}"; Flags: ignoreversion


[Dirs]
; 🔥 NUEVO: Aseguramos la creación de las carpetas de trabajo con permisos de administrador
Name: "{app}\backup"
Name: "{app}\logs"


[Icons]
; ICONOS CON RUTA EXPLÍCITA AL .ICO
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{group}\Reparar MySQL"; Filename: "{app}\reparar_mysql.bat"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

[Run]
; Nada aquí: control total desde [Code]

[UninstallRun]
Filename: "{sys}\sc.exe"; Parameters: "stop MySQL_DonAtilio"; Flags: runhidden
Filename: "{sys}\sc.exe"; Parameters: "delete MySQL_DonAtilio"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\mysql\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\backup" ;
[Code]
var
  ProgressPage: TOutputProgressWizardPage;
  MySQLInstallSuccess: Boolean;
  SeedDataSuccess: Boolean;
  AdminFixSuccess: Boolean;

procedure SleepMs(ms: Integer);
begin
  Sleep(ms);
end;

function ExecOk(const FileName, Params, WorkDir: string; Show: Integer): Boolean;
var Code: Integer;
begin
  Result := Exec(FileName, Params, WorkDir, Show, ewWaitUntilTerminated, Code) and (Code = 0);
end;

function InstalarMySQL(): Boolean;
var Code: Integer;
begin
  Result := False;
  ProgressPage.SetText('Configurando base de datos...', '');
  ProgressPage.SetProgress(0, 100);

  Log('Ejecutando setup_mysql.bat');
  if Exec('cmd.exe', '/c "' + ExpandConstant('{app}\setup_mysql.bat') + '"',
           ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, Code) then
  begin
    Log(Format('setup_mysql.bat terminó con código %d',[Code]));
    SleepMs(3000);

    if ExecOk('sc.exe', 'query MySQL_DonAtilio', '', SW_HIDE) then
    begin
      Log('✔ Servicio MySQL_DonAtilio creado/registrado');
      Result := True;
    end
    else
      Log('✗ No se pudo verificar el servicio MySQL_DonAtilio');
  end
  else
    Log('✗ Error al lanzar setup_mysql.bat');

  ProgressPage.SetProgress(100, 100);
end;

function CargarDatosIniciales(): Boolean;
var 
  Code: Integer;
  AppPath: String;
  ExePath: String;
begin
  Result := False;
  ProgressPage.SetText('Cargando datos iniciales...', 'Usuarios, categorías...');
  ProgressPage.SetProgress(0, 100);

  AppPath := ExpandConstant('{app}');
  ExePath := AppPath + '\{#MyAppExeName}';

  Log('=== INICIO SEED DATA ===');
  Log('Ejecutable: ' + ExePath);
  Log('Directorio: ' + AppPath);
  Log('Comando: ' + ExePath + ' --seed-data');
  
  if Exec(ExePath, '--seed-data', AppPath, SW_HIDE, ewWaitUntilTerminated, Code) then
  begin
    Log(Format('--seed-data terminó con código %d', [Code]));
    
    if Code = 0 then
    begin
      Log('✔ Datos iniciales cargados correctamente');
      Result := True;
    end
    else
    begin
      Log(Format('✗ Seed data falló con código %d', [Code]));
      Result := False;
    end;
  end
  else
  begin
    Log('✗ No se pudo ejecutar --seed-data (Exec falló)');
    Result := False;
  end;

  Log('=== FIN SEED DATA ===');
  ProgressPage.SetProgress(100, 100);
end;

function GarantizarAdmin(): Boolean;
var
  Params: string;
  Hash: string;
begin
  Result := False;
  ProgressPage.SetText('Asegurando usuario administrador...', '');
  ProgressPage.SetProgress(0, 100);

  { Hash bcrypt para "admin123" (cost 12) }
  Hash := '$2b$12$tEa6owvg3LQbn5ZmLewhAe0anU6hj9ygpkKajh1p9H2YbU9QBvKnS';

  { UPSERT: crea admin si no existe y, si existe, fuerza contraseña/activo/rol }
  Params :=
    '-u root --port=3307 --protocol=TCP -e ' +
    '"INSERT INTO supermercado_don_atilio.usuario (nombre, `contraseña`, id_rol, activo) ' +
    'VALUES (''admin'', ''' + Hash + ''', 1, 1) ' +
    'ON DUPLICATE KEY UPDATE `contraseña`=VALUES(`contraseña`), id_rol=1, activo=1;"';

  if ExecOk(ExpandConstant('{app}\mysql\bin\mysql.exe'), Params, ExpandConstant('{app}'), SW_HIDE) then
  begin
    Log('✔ Usuario admin garantizado (admin/admin123)');
    Result := True;
  end
  else
    Log('✗ No se pudo garantizar el admin');

  ProgressPage.SetProgress(100, 100);
end;

function VerificarInstalacion(): Boolean;
begin
  Result := False;
  ProgressPage.SetText('Verificando instalación...', '');
  ProgressPage.SetProgress(0, 100);

  if ExecOk('sc.exe', 'query MySQL_DonAtilio', '', SW_HIDE) then
  begin
    Log('✔ Servicio MySQL_DonAtilio OK');
    SleepMs(1000);

    if ExecOk(ExpandConstant('{app}\mysql\bin\mysql.exe'),
              '-u root --port=3307 --protocol=TCP -e "SELECT 1;"',
              ExpandConstant('{app}'), SW_HIDE) then
    begin
      Log('✔ MySQL responde');
      if ExecOk(ExpandConstant('{app}\mysql\bin\mysql.exe'),
                '-u root --port=3307 --protocol=TCP -e "USE supermercado_don_atilio; SELECT COUNT(*) FROM usuario;"',
                ExpandConstant('{app}'), SW_HIDE) then
      begin
        Log('✔ Base con tablas/datos');
        Result := True;
      end;
    end;
  end
  else
    Log('✗ Servicio MySQL_DonAtilio NO OK');

  ProgressPage.SetProgress(100, 100);
end;

procedure InitializeWizard();
begin
  ProgressPage := CreateOutputProgressPage('Configurando Sistema',
    'Por favor espere mientras se prepara la base de datos...');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Intentos: Integer;
  Msg: String;
begin
  if CurStep = ssPostInstall then
  begin
    MySQLInstallSuccess := False;
    SeedDataSuccess := False;
    AdminFixSuccess := False;

    ProgressPage.Show;
    try
      { Paso 1: MySQL }
      ProgressPage.SetText('Paso 1/4: Instalando MySQL...', '');
      Intentos := 0;
      while (Intentos < 2) and (not MySQLInstallSuccess) do
      begin
        MySQLInstallSuccess := InstalarMySQL();
        if not MySQLInstallSuccess then
        begin
          Intentos := Intentos + 1;
          if Intentos < 2 then SleepMs(2000);
        end;
      end;

      if not MySQLInstallSuccess then
      begin
        Msg :=
          'No se pudo instalar MySQL correctamente.'#13#10#13#10 +
          'Para completar manualmente:'#13#10 +
          '1) Abrí "Reparar MySQL" desde el menú Inicio.'#13#10 +
          '2) Luego ejecutá manualmente:'#13#10 +
          '   cd "C:\Program Files\Sistema Cobros Don Atilio"'#13#10 +
          '   SistemaCobrosDonAtilio.exe --seed-data';
        MsgBox(Msg, mbError, MB_OK);
        Exit;
      end;

      { Paso 2: Seed (INTEGRADO EN EL .EXE) }
      ProgressPage.SetText('Paso 2/4: Cargando datos iniciales...', '');
      SeedDataSuccess := CargarDatosIniciales();

      { Paso 3: Garantizar admin (por si el seed falló) }
      ProgressPage.SetText('Paso 3/4: Asegurando admin/admin123...', '');
      AdminFixSuccess := GarantizarAdmin();

      { Paso 4: Verificación }
      ProgressPage.SetText('Paso 4/4: Verificando instalación...', '');
      if VerificarInstalacion() then
        Log('✔✔✔ Instalación verificada')
      else
        Log('⚠ Verificación con advertencias');
    finally
      ProgressPage.Hide;
    end;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  okTxt: String;
begin
  if CurPageID = wpFinished then
  begin
    // CORRECCIÓN: Concatenación correcta de strings para evitar error de compilación
    okTxt :=
      '¡Instalación completada!'#13#10#13#10 +
      'Podés abrir "Sistema Cobros Don Atilio" desde el acceso directo.'#13#10#13#10 +
      'Credenciales:'#13#10 +
      '• Usuario: admin | ' +
      'Contraseña: admin123'#13#10 +
      '• Puerto MySQL: 3307';

    if MySQLInstallSuccess and (SeedDataSuccess or AdminFixSuccess) then
      WizardForm.FinishedLabel.Caption := okTxt
    else if MySQLInstallSuccess and not (SeedDataSuccess or AdminFixSuccess) then
      WizardForm.FinishedLabel.Caption :=
        'MySQL se instaló, pero falta cargar datos.'#13#10#13#10 +
        'Abrí CMD como Administrador y ejecutá:'#13#10 +
        'cd "' + ExpandConstant('{app}') + '"'#13#10 +
        ExpandConstant('{#MyAppExeName}') + ' --seed-data'
    else
      WizardForm.FinishedLabel.Caption :=
        'La instalación necesita reparación.'#13#10#13#10 +
        'Ejecutá "Reparar MySQL" desde el menú Inicio.';
  end;
end;