[Setup]
AppName=Merger CLI
AppVersion=4.0.0-alpha
DefaultDirName={autopf}\MergerCLI
DefaultGroupName=Merger CLI
OutputDir=..\dist
OutputBaseFilename=merger-cli-windows-installer
Compression=lzma
SolidCompression=yes
ChangesEnvironment=yes

[Files]
Source: "..\dist\merger-cli.exe"; DestDir: "{app}"; DestName: "merger.exe"; Flags: ignoreversion

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
    if CurStep = ssPostInstall then
        AddToPath(ExpandConstant('{app}'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
    if CurUninstallStep = usPostUninstall then
        RemoveFromPath(ExpandConstant('{app}'));
end;
