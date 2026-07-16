#include "SpectRunAction.hh"

#include "G4GenericMessenger.hh"
#include "G4Run.hh"
#include "g4root.hh"

SpectRunAction::SpectRunAction()
  : G4UserRunAction(),
    fOutputFile("spect_output.root"),
    fMessenger(0)
{
  fMessenger = new G4GenericMessenger(this, "/spect/output/", "SPECT output control");
  fMessenger->DeclareProperty("file", fOutputFile, "ROOT output file name");
}

SpectRunAction::~SpectRunAction()
{
  delete fMessenger;
}

void SpectRunAction::BeginOfRunAction(const G4Run*)
{
  G4AnalysisManager* analysis = G4AnalysisManager::Instance();
  analysis->SetVerboseLevel(1);
  analysis->SetFirstNtupleId(0);
  analysis->OpenFile(fOutputFile);

  analysis->CreateNtuple("tree_chroma", "LSO energy-deposition hits for Chroma");
  analysis->CreateNtupleDColumn("event");
  analysis->CreateNtupleDColumn("hits");
  analysis->CreateNtupleDColumn("xpos");
  analysis->CreateNtupleDColumn("ypos");
  analysis->CreateNtupleDColumn("zpos");
  analysis->CreateNtupleDColumn("time");
  analysis->CreateNtupleDColumn("edep");
  analysis->CreateNtupleDColumn("energy");
  analysis->CreateNtupleDColumn("x_momentum");
  analysis->CreateNtupleDColumn("y_momentum");
  analysis->CreateNtupleDColumn("z_momentum");
  analysis->CreateNtupleDColumn("particle_name");
  analysis->CreateNtupleDColumn("PDG");
  analysis->CreateNtupleDColumn("trackID");
  analysis->FinishNtuple();
}

void SpectRunAction::EndOfRunAction(const G4Run*)
{
  G4AnalysisManager* analysis = G4AnalysisManager::Instance();
  analysis->Write();
  analysis->CloseFile();
}
