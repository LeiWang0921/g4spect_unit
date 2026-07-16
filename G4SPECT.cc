#include "SpectActionInitialization.hh"
#include "SpectDetectorConstruction.hh"
#include "SpectPhysicsList.hh"

#include "G4RunManager.hh"
#include "G4UImanager.hh"
#include "Randomize.hh"

#ifdef G4VIS_USE
#include "G4VisExecutive.hh"
#endif

#ifdef G4UI_USE
#include "G4UIExecutive.hh"
#endif

int main(int argc, char** argv)
{
  G4Random::setTheEngine(new CLHEP::RanecuEngine);

  G4RunManager* runManager = new G4RunManager;
  runManager->SetUserInitialization(new SpectDetectorConstruction);
  runManager->SetUserInitialization(new SpectPhysicsList);
  runManager->SetUserInitialization(new SpectActionInitialization);
  runManager->Initialize();

#ifdef G4VIS_USE
  G4VisManager* visManager = new G4VisExecutive;
  visManager->Initialize();
#endif

  G4UImanager* uiManager = G4UImanager::GetUIpointer();
  if (argc == 1) {
#ifdef G4UI_USE
    G4UIExecutive* ui = new G4UIExecutive(argc, argv);
    ui->SessionStart();
    delete ui;
#endif
  } else {
    G4String command = "/control/execute ";
    G4String fileName = argv[1];
    uiManager->ApplyCommand(command + fileName);
  }

#ifdef G4VIS_USE
  delete visManager;
#endif
  delete runManager;
  return 0;
}
