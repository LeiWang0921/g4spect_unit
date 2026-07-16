#include "SpectPhysicsList.hh"

#include "G4DecayPhysics.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4EmParameters.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4StepLimiterPhysics.hh"
#include "G4SystemOfUnits.hh"

SpectPhysicsList::SpectPhysicsList()
  : G4VModularPhysicsList()
{
  defaultCutValue = 1.0*um;
  SetVerboseLevel(1);

  G4EmParameters* params = G4EmParameters::Instance();
  params->SetMaxEnergy(100.0*GeV);
  params->SetNumberOfBinsPerDecade(20);
  params->SetFluo(true);
  params->SetAuger(true);
  params->SetPixe(true);

  RegisterPhysics(new G4EmLivermorePhysics());
  RegisterPhysics(new G4DecayPhysics());
  RegisterPhysics(new G4RadioactiveDecayPhysics());
  RegisterPhysics(new G4StepLimiterPhysics());
}

SpectPhysicsList::~SpectPhysicsList()
{
}

void SpectPhysicsList::SetCuts()
{
  SetCutValue(1.0*um, "gamma");
  SetCutValue(1.0*um, "e-");
  SetCutValue(1.0*um, "e+");
}
