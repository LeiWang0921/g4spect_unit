#include "SpectDetectorConstruction.hh"
#include "SpectSensitiveDetector.hh"

#include "G4Box.hh"
#include "G4Element.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SDManager.hh"
#include "G4SubtractionSolid.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4VisAttributes.hh"

#include <sstream>

SpectDetectorConstruction::SpectDetectorConstruction()
  : G4VUserDetectorConstruction(),
    fLSOLogical(0),
    fWorldMaterial(0),
    fLeadMaterial(0),
    fLSOMaterial(0),
    fGelMaterial(0),
    fSiPMMaterial(0)
{
}

SpectDetectorConstruction::~SpectDetectorConstruction()
{
}

G4Material* SpectDetectorConstruction::BuildLSO()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Element* lu = nist->FindOrBuildElement("Lu");
  G4Element* si = nist->FindOrBuildElement("Si");
  G4Element* o = nist->FindOrBuildElement("O");

  G4Material* lso = new G4Material("LSO", 7.40*g/cm3, 3);
  lso->AddElement(lu, 2);
  lso->AddElement(si, 1);
  lso->AddElement(o, 5);
  return lso;
}

G4Material* SpectDetectorConstruction::BuildOpticalGel()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Element* h = nist->FindOrBuildElement("H");
  G4Element* c = nist->FindOrBuildElement("C");
  G4Element* o = nist->FindOrBuildElement("O");
  G4Element* si = nist->FindOrBuildElement("Si");

  G4Material* gel = new G4Material("OpticalGel", 1.03*g/cm3, 4);
  gel->AddElement(c, 2);
  gel->AddElement(h, 6);
  gel->AddElement(o, 1);
  gel->AddElement(si, 1);
  return gel;
}

void SpectDetectorConstruction::DefineMaterials()
{
  G4NistManager* nist = G4NistManager::Instance();
  fWorldMaterial = nist->FindOrBuildMaterial("G4_AIR");
  fLeadMaterial = nist->FindOrBuildMaterial("G4_Pb");
  fSiPMMaterial = nist->FindOrBuildMaterial("G4_Si");
  fLSOMaterial = BuildLSO();
  fGelMaterial = BuildOpticalGel();
}

G4VPhysicalVolume* SpectDetectorConstruction::Construct()
{
  DefineMaterials();

  G4Box* worldSolid = new G4Box("world", 200*mm, 200*mm, 200*mm);
  G4LogicalVolume* worldLogical =
    new G4LogicalVolume(worldSolid, fWorldMaterial, "world_log");
  G4VPhysicalVolume* worldPhysical =
    new G4PVPlacement(0, G4ThreeVector(), "world_phys", worldLogical, 0, false, 0);

  const G4double detectorXY = 32.0*mm;
  const G4double lsoThickness = 10.0*mm;
  G4Box* lsoSolid =
    new G4Box("LSO_solid", detectorXY/2.0, detectorXY/2.0, lsoThickness/2.0);
  fLSOLogical = new G4LogicalVolume(lsoSolid, fLSOMaterial, "LSO_log");
  new G4PVPlacement(0, G4ThreeVector(0, 0, 0), "LSO_phys",
                    fLSOLogical, worldPhysical, false, 0);

  const G4double gelThickness = 0.5*mm;
  G4Box* gelSolid =
    new G4Box("OpticalGel_solid", detectorXY/2.0, detectorXY/2.0, gelThickness/2.0);
  G4LogicalVolume* gelLogical =
    new G4LogicalVolume(gelSolid, fGelMaterial, "OpticalGel_log");
  new G4PVPlacement(0, G4ThreeVector(0, 0, 5.25*mm), "OpticalGel_phys",
                    gelLogical, worldPhysical, false, 0);

  const G4double sipmThickness = 1.0*mm;
  G4Box* sipmSolid =
    new G4Box("SiPM_solid", detectorXY/2.0, detectorXY/2.0, sipmThickness/2.0);
  G4LogicalVolume* sipmLogical =
    new G4LogicalVolume(sipmSolid, fSiPMMaterial, "SiPM_log");
  new G4PVPlacement(0, G4ThreeVector(0, 0, 6.0*mm), "SiPM_phys",
                    sipmLogical, worldPhysical, false, 0);

  const G4double collimatorXY = 32.0*mm;
  const G4double collimatorLength = 25.0*mm;
  G4VSolid* collimatorSolid =
    new G4Box("Collimator_block", collimatorXY/2.0, collimatorXY/2.0, collimatorLength/2.0);
  G4Box* holeSolid = new G4Box("Collimator_square_hole", 1.2*mm, 1.2*mm, 13.0*mm);

  const G4int halfGrid = 4;
  const G4double pitch = 3.2*mm;
  for (G4int ix = -halfGrid; ix <= halfGrid; ++ix) {
    for (G4int iy = -halfGrid; iy <= halfGrid; ++iy) {
      std::ostringstream name;
      name << "Collimator_hole_sub_" << ix << "_" << iy;
      G4ThreeVector offset(ix*pitch, iy*pitch, 0);
      collimatorSolid =
        new G4SubtractionSolid(name.str(), collimatorSolid, holeSolid, 0, offset);
    }
  }

  G4LogicalVolume* collimatorLogical =
    new G4LogicalVolume(collimatorSolid, fLeadMaterial, "Collimator_log");
  new G4PVPlacement(0, G4ThreeVector(0, 0, -19.0*mm), "Collimator_phys",
                    collimatorLogical, worldPhysical, false, 0);

  worldLogical->SetVisAttributes(G4VisAttributes::Invisible);
  fLSOLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.0, 0.7, 1.0, 0.4)));
  gelLogical->SetVisAttributes(new G4VisAttributes(G4Colour(1.0, 1.0, 1.0, 0.3)));
  sipmLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.1, 0.1, 0.1)));
  collimatorLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.45, 0.45, 0.45)));

  return worldPhysical;
}

void SpectDetectorConstruction::ConstructSDandField()
{
  SpectSensitiveDetector* lsoSD = new SpectSensitiveDetector("/SPECT/LSOSD");
  G4SDManager::GetSDMpointer()->AddNewDetector(lsoSD);
  if (fLSOLogical) {
    SetSensitiveDetector(fLSOLogical, lsoSD);
  }
}
