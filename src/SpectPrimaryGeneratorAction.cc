#include "SpectPrimaryGeneratorAction.hh"

#include "G4Event.hh"
#include "G4GeneralParticleSource.hh"

SpectPrimaryGeneratorAction::SpectPrimaryGeneratorAction()
  : G4VUserPrimaryGeneratorAction(),
    fSource(new G4GeneralParticleSource)
{
}

SpectPrimaryGeneratorAction::~SpectPrimaryGeneratorAction()
{
  delete fSource;
}

void SpectPrimaryGeneratorAction::GeneratePrimaries(G4Event* event)
{
  fSource->GeneratePrimaryVertex(event);
}
