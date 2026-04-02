[Setup]
AppName=Merger CLI
AppVersion=4.0.0-alpha.2

AppPublisher=Diogo Toporcov
AppPublisherURL=https://github.com/diogotoporcov/merger-cli
AppSupportURL=https://github.com/diogotoporcov/merger-cli/issues
AppUpdatesURL=https://github.com/diogotoporcov/merger-cli/releases
AppContact=diogotoporcov@gmail.com

DefaultDirName={localappdata}\Programs\MergerCLI
DefaultGroupName=Merger CLI

OutputDir=..\dist
OutputBaseFilename=merger-cli-windows-installer

Compression=lzma
SolidCompression=yes
ChangesEnvironment=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableProgramGroupPage=yes

VersionInfoVersion=4.0.0.2
VersionInfoProductVersion=4.0.0.2
VersionInfoProductTextVersion=4.0.0-alpha.2
VersionInfoCompany=Diogo Losacco Toporcov
VersionInfoDescription=Installer for Merger CLI
VersionInfoProductName=Merger CLI
VersionInfoCopyright=Copyright (C) 2026 Diogo Losacco Toporcov

; Optional if you have these files:
; SetupIconFile=..\assets\merger.ico
; LicenseFile=..\LICENSE.txt
; InfoBeforeFile=..\INSTALLER-README.txt
; InfoAfterFile=..\RELEASE-NOTES.txt

UninstallDisplayIcon={app}\merger.exe

[Tasks]
Name: "addtopath"; Description: "Add Merger CLI to PATH"; Flags: checkedonce

[Files]
Source: "..\dist\merger-cli\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Merger CLI"; Filename: "{app}\merger.exe"

[Code]
procedure AddToPath(PathToAdd: string);
var
    OldPath: string;
    NewPath: string;
begin
    if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OldPath) then
        OldPath := '';

    if Pos(';' + Uppercase(PathToAdd) + ';', ';' + Uppercase(OldPath) + ';') = 0 then
    begin
        NewPath := OldPath;
        if (NewPath <> '') and (NewPath[Length(NewPath)] <> ';') then
            NewPath := NewPath + ';';
        NewPath := NewPath + PathToAdd;
        RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', NewPath);
    end;
end;

procedure RemoveFromPath(PathToRemove: string);
var
    OldPath: string;
    NewPath: string;
    P: Integer;
begin
    if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OldPath) then
    begin
        NewPath := OldPath;
        P := Pos(';' + Uppercase(PathToRemove) + ';', ';' + Uppercase(NewPath) + ';');
        if P <> 0 then
        begin
            Delete(NewPath, P, Length(PathToRemove) + 1);
            RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', NewPath);
        end;
    end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
    if (CurStep = ssPostInstall) and WizardIsTaskSelected('addtopath') then
        AddToPath(ExpandConstant('{app}'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
    if CurUninstallStep = usPostUninstall then
        RemoveFromPath(ExpandConstant('{app}'));
end;