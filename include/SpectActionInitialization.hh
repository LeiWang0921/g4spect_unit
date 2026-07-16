#ifndef SpectActionInitialization_h
#define SpectActionInitialization_h 1

#include "G4VUserActionInitialization.hh"

class SpectActionInitialization : public G4VUserActionInitialization
{
public:
  SpectActionInitialization();
  virtual ~SpectActionInitialization();

  virtual void Build() const;
  virtual void BuildForMaster() const;
};

#endif
