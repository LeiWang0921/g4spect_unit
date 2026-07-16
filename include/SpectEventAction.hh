#ifndef SpectEventAction_h
#define SpectEventAction_h 1

#include "G4UserEventAction.hh"

class G4Event;

class SpectEventAction : public G4UserEventAction
{
public:
  SpectEventAction();
  virtual ~SpectEventAction();

  virtual void EndOfEventAction(const G4Event* event);

private:
  int fHitsCollectionID;
};

#endif
