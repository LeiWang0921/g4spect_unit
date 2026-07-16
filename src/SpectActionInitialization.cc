#include "SpectActionInitialization.hh"
#include "SpectEventAction.hh"
#include "SpectPrimaryGeneratorAction.hh"
#include "SpectRunAction.hh"

SpectActionInitialization::SpectActionInitialization()
  : G4VUserActionInitialization()
{
}

SpectActionInitialization::~SpectActionInitialization()
{
}

void SpectActionInitialization::Build() const
{
  SetUserAction(new SpectPrimaryGeneratorAction);
  SetUserAction(new SpectRunAction);
  SetUserAction(new SpectEventAction);
}

void SpectActionInitialization::BuildForMaster() const
{
  SetUserAction(new SpectRunAction);
}
