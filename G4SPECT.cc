#include "SpectActionInitialization.hh"
#include "SpectDetectorConstruction.hh"
#include "SpectPhysicsList.hh"

#include "G4RunManager.hh"
#include "G4UImanager.hh"
#include "Randomize.hh"

#include <cstdlib>
#include <iostream>

#ifdef G4VIS_USE
#include "G4VisExecutive.hh"
#endif

#ifdef G4UI_USE
#include "G4UIExecutive.hh"
#endif

namespace
{
G4bool EnvEnabled(const char* name)
{
  const char* value = std::getenv(name);
  if (!value || value[0] == '\0') {
    return false;
  }
  G4String text(value);
  return text != "0" && text != "false" && text != "FALSE";
}
}

int main(int argc, char** argv)
{
  G4Random::setTheEngine(new CLHEP::RanecuEngine);

  G4bool enableDicomPhantom = EnvEnabled("G4SPECT_ENABLE_DICOM_PHANTOM");
  G4bool enableHumanPhantom = EnvEnabled("G4SPECT_ENABLE_HUMAN_PHANTOM");
  G4String macroFile;
  for (G4int i = 1; i < argc; ++i) {
    G4String arg(argv[i]);
    if (arg == "--dicom-phantom") {
      enableDicomPhantom = true;
    } else if (arg == "--human-phantom") {
      enableHumanPhantom = true;
    } else if (macroFile.empty()) {
      macroFile = arg;
    }
  }

  if (enableDicomPhantom && enableHumanPhantom) {
    std::cerr << "Cannot enable both --dicom-phantom and --human-phantom in the same run. "
              << "Pick one phantom geometry." << std::endl;
    return 1;
  }

  G4RunManager* runManager = new G4RunManager;
  runManager->SetUserInitialization(
    new SpectDetectorConstruction(enableDicomPhantom, enableHumanPhantom));
  runManager->SetUserInitialization(new SpectPhysicsList);
  runManager->SetUserInitialization(new SpectActionInitialization);
  runManager->Initialize();

#ifdef G4VIS_USE
  G4VisManager* visManager = new G4VisExecutive;
  visManager->Initialize();
#endif

  G4UImanager* uiManager = G4UImanager::GetUIpointer();
  if (macroFile.empty()) {
#ifdef G4UI_USE
    G4UIExecutive* ui = new G4UIExecutive(argc, argv);
    ui->SessionStart();
    delete ui;
#endif
  } else {
    G4String command = "/control/execute ";
    uiManager->ApplyCommand(command + macroFile);
  }

#ifdef G4VIS_USE
  delete visManager;
#endif
  delete runManager;
  return 0;
}
