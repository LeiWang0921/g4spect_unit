#include "SpectEventAction.hh"
#include "SpectHit.hh"

#include "G4Event.hh"
#include "G4HCofThisEvent.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "g4root.hh"

namespace
{
G4double ParticleIndex(const G4String& name)
{
  if (name == "gamma") return 1.0;
  if (name == "neutron") return 2.0;
  if (name == "e-") return 3.0;
  if (name == "e+") return 4.0;
  return 5.0;
}
}

SpectEventAction::SpectEventAction()
  : G4UserEventAction(),
    fHitsCollectionID(-1)
{
}

SpectEventAction::~SpectEventAction()
{
}

void SpectEventAction::EndOfEventAction(const G4Event* event)
{
  if (fHitsCollectionID < 0) {
    fHitsCollectionID = G4SDManager::GetSDMpointer()->GetCollectionID("lsoHitsCollection");
  }

  G4HCofThisEvent* hce = event->GetHCofThisEvent();
  if (!hce) return;

  SpectHitsCollection* hitsCollection =
    static_cast<SpectHitsCollection*>(hce->GetHC(fHitsCollectionID));
  if (!hitsCollection) return;

  G4AnalysisManager* analysis = G4AnalysisManager::Instance();
  const G4double eventID = static_cast<G4double>(event->GetEventID());

  for (G4int i = 0; i < hitsCollection->entries(); ++i) {
    SpectHit* hit = (*hitsCollection)[i];
    const G4ThreeVector& pos = hit->GetPos();
    const G4ThreeVector& mom = hit->GetMomentum();

    analysis->FillNtupleDColumn(0, 0, eventID);
    analysis->FillNtupleDColumn(0, 1, static_cast<G4double>(i));
    analysis->FillNtupleDColumn(0, 2, pos.x()/mm);
    analysis->FillNtupleDColumn(0, 3, pos.y()/mm);
    analysis->FillNtupleDColumn(0, 4, pos.z()/mm);
    analysis->FillNtupleDColumn(0, 5, hit->GetTime()/ns);
    analysis->FillNtupleDColumn(0, 6, hit->GetEdep()/keV);
    analysis->FillNtupleDColumn(0, 7, hit->GetParticleEnergy()/keV);
    analysis->FillNtupleDColumn(0, 8, mom.x()/keV);
    analysis->FillNtupleDColumn(0, 9, mom.y()/keV);
    analysis->FillNtupleDColumn(0, 10, mom.z()/keV);
    analysis->FillNtupleDColumn(0, 11, ParticleIndex(hit->GetParticleName()));
    analysis->FillNtupleDColumn(0, 12, static_cast<G4double>(hit->GetParticlePDG()));
    analysis->FillNtupleDColumn(0, 13, static_cast<G4double>(hit->GetTrackID()));
    analysis->AddNtupleRow(0);
  }
}
