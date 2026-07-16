#ifndef SpectHit_h
#define SpectHit_h 1

#include "G4THitsCollection.hh"
#include "G4ThreeVector.hh"
#include "G4VHit.hh"
#include "globals.hh"

class SpectHit : public G4VHit
{
public:
  SpectHit();
  virtual ~SpectHit();

  void SetEdep(G4double value) { fEdep = value; }
  void SetPos(const G4ThreeVector& value) { fPos = value; }
  void SetTime(G4double value) { fTime = value; }
  void SetParticleName(const G4String& value) { fParticleName = value; }
  void SetParticlePDG(G4int value) { fParticlePDG = value; }
  void SetParticleEnergy(G4double value) { fParticleEnergy = value; }
  void SetMomentum(const G4ThreeVector& value) { fMomentum = value; }
  void SetTrackID(G4int value) { fTrackID = value; }

  G4double GetEdep() const { return fEdep; }
  const G4ThreeVector& GetPos() const { return fPos; }
  G4double GetTime() const { return fTime; }
  const G4String& GetParticleName() const { return fParticleName; }
  G4int GetParticlePDG() const { return fParticlePDG; }
  G4double GetParticleEnergy() const { return fParticleEnergy; }
  const G4ThreeVector& GetMomentum() const { return fMomentum; }
  G4int GetTrackID() const { return fTrackID; }

private:
  G4double fEdep;
  G4ThreeVector fPos;
  G4double fTime;
  G4String fParticleName;
  G4int fParticlePDG;
  G4double fParticleEnergy;
  G4ThreeVector fMomentum;
  G4int fTrackID;
};

typedef G4THitsCollection<SpectHit> SpectHitsCollection;

#endif
