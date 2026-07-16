#ifndef SpectRunAction_h
#define SpectRunAction_h 1

#include "G4UserRunAction.hh"
#include "globals.hh"

class G4GenericMessenger;
class G4Run;

class SpectRunAction : public G4UserRunAction
{
public:
  SpectRunAction();
  virtual ~SpectRunAction();

  virtual void BeginOfRunAction(const G4Run* run);
  virtual void EndOfRunAction(const G4Run* run);

private:
  G4String fOutputFile;
  G4GenericMessenger* fMessenger;
};

#endif
