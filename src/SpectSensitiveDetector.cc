#include "SpectSensitiveDetector.hh"

#include "G4HCofThisEvent.hh"
#include "G4OpticalPhoton.hh"
#include "G4SDManager.hh"
#include "G4Step.hh"

SpectSensitiveDetector::SpectSensitiveDetector(const G4String& name)
  : G4VSensitiveDetector(name),
    fHitsCollection(0)
{
  collectionName.insert("lysoHitsCollection");
}

SpectSensitiveDetector::~SpectSensitiveDetector()
{
}

void SpectSensitiveDetector::Initialize(G4HCofThisEvent*)
{
  fHitsCollection = new SpectHitsCollection(SensitiveDetectorName, collectionName[0]);
}

G4bool SpectSensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*)
{
  G4Track* track = step->GetTrack();
  if (track->GetDefinition() == G4OpticalPhoton::OpticalPhotonDefinition()) {
    return false;
  }

  if (track->GetCurrentStepNumber() == 1) {
    G4StepPoint* preStep = step->GetPreStepPoint();
    SpectHit* firstHit = new SpectHit;
    firstHit->SetEdep(0.0);
    firstHit->SetPos(preStep->GetPosition());
    firstHit->SetTime(preStep->GetLocalTime());
    firstHit->SetParticleName(track->GetDefinition()->GetParticleName());
    firstHit->SetParticlePDG(track->GetDefinition()->GetPDGEncoding());
    firstHit->SetParticleEnergy(preStep->GetKineticEnergy());
    firstHit->SetMomentum(preStep->GetMomentum());
    firstHit->SetTrackID(track->GetTrackID());
    fHitsCollection->insert(firstHit);
  }

  G4StepPoint* preStep = step->GetPreStepPoint();
  G4StepPoint* postStep = step->GetPostStepPoint();
  SpectHit* hit = new SpectHit;
  hit->SetEdep(step->GetTotalEnergyDeposit());
  hit->SetPos(postStep->GetPosition());
  hit->SetTime(preStep->GetLocalTime());
  hit->SetParticleName(track->GetDefinition()->GetParticleName());
  hit->SetParticlePDG(track->GetDefinition()->GetPDGEncoding());
  hit->SetParticleEnergy(preStep->GetKineticEnergy());
  hit->SetMomentum(postStep->GetMomentum());
  hit->SetTrackID(track->GetTrackID());
  fHitsCollection->insert(hit);

  return true;
}

void SpectSensitiveDetector::EndOfEvent(G4HCofThisEvent* hce)
{
  static G4int hitsCollectionID = -1;
  if (hitsCollectionID < 0) {
    hitsCollectionID = G4SDManager::GetSDMpointer()->GetCollectionID(collectionName[0]);
  }
  hce->AddHitsCollection(hitsCollectionID, fHitsCollection);
}
