#include "SpectHit.hh"

SpectHit::SpectHit()
  : G4VHit(),
    fEdep(0.0),
    fPos(),
    fTime(0.0),
    fParticleName(""),
    fParticlePDG(0),
    fParticleEnergy(0.0),
    fMomentum(),
    fTrackID(-1)
{
}

SpectHit::~SpectHit()
{
}
