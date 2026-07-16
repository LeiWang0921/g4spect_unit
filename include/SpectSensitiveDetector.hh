#ifndef SpectSensitiveDetector_h
#define SpectSensitiveDetector_h 1

#include "G4VSensitiveDetector.hh"
#include "SpectHit.hh"

class G4HCofThisEvent;
class G4Step;
class G4TouchableHistory;

class SpectSensitiveDetector : public G4VSensitiveDetector
{
public:
  SpectSensitiveDetector(const G4String& name);
  virtual ~SpectSensitiveDetector();

  virtual void Initialize(G4HCofThisEvent* hce);
  virtual G4bool ProcessHits(G4Step* step, G4TouchableHistory* history);
  virtual void EndOfEvent(G4HCofThisEvent* hce);

private:
  SpectHitsCollection* fHitsCollection;
};

#endif
