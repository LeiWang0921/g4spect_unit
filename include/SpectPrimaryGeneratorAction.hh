#ifndef SpectPrimaryGeneratorAction_h
#define SpectPrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"

class G4Event;
class G4GeneralParticleSource;

class SpectPrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
public:
  SpectPrimaryGeneratorAction();
  virtual ~SpectPrimaryGeneratorAction();

  virtual void GeneratePrimaries(G4Event* event);

private:
  G4GeneralParticleSource* fSource;
};

#endif
