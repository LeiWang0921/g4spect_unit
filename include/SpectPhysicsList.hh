#ifndef SpectPhysicsList_h
#define SpectPhysicsList_h 1

#include "G4VModularPhysicsList.hh"

class SpectPhysicsList : public G4VModularPhysicsList
{
public:
  SpectPhysicsList();
  virtual ~SpectPhysicsList();

  virtual void SetCuts();
};

#endif
