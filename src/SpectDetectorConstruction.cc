#include "SpectDetectorConstruction.hh"
#include "SpectSensitiveDetector.hh"

#include "G4Box.hh"
#include "G4Element.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4VisAttributes.hh"

SpectDetectorConstruction::SpectDetectorConstruction()
  : G4VUserDetectorConstruction(),
    fLYSOLogical(0),
    fWorldMaterial(0),
    fLeadMaterial(0),
    fLYSOMaterial(0),
    fGelMaterial(0),
    fSiPMMaterial(0)
{
}

SpectDetectorConstruction::~SpectDetectorConstruction()
{
}

G4Material* SpectDetectorConstruction::BuildLYSO()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Element* lu = nist->FindOrBuildElement("Lu");
  G4Element* y = nist->FindOrBuildElement("Y");
  G4Element* si = nist->FindOrBuildElement("Si");
  G4Element* o = nist->FindOrBuildElement("O");

  G4Material* lyso = new G4Material("LYSO", 7.10*g/cm3, 4);
  lyso->AddElement(lu, 0.7144);
  lyso->AddElement(y, 0.0403);
  lyso->AddElement(si, 0.0637);
  lyso->AddElement(o, 0.1816);
  return lyso;
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
  fLYSOMaterial = BuildLYSO();
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

  const G4double detectorXY = 64.0*mm;
  const G4double lysoThickness = 10.0*mm;
  const G4double lysoCenterZ = 140.0*mm;
  G4Box* lysoSolid =
    new G4Box("LYSO_solid", detectorXY/2.0, detectorXY/2.0, lysoThickness/2.0);
  fLYSOLogical = new G4LogicalVolume(lysoSolid, fLYSOMaterial, "LYSO_log");
  new G4PVPlacement(0, G4ThreeVector(0, 0, lysoCenterZ), "LYSO_phys",
                    fLYSOLogical, worldPhysical, false, 0);

  const G4double gelThickness = 0.5*mm;
  const G4double gelCenterZ = 145.25*mm;
  G4Box* gelSolid =
    new G4Box("OpticalGel_solid", detectorXY/2.0, detectorXY/2.0, gelThickness/2.0);
  G4LogicalVolume* gelLogical =
    new G4LogicalVolume(gelSolid, fGelMaterial, "OpticalGel_log");
  new G4PVPlacement(0, G4ThreeVector(0, 0, gelCenterZ), "OpticalGel_phys",
                    gelLogical, worldPhysical, false, 0);

  const G4double sipmThickness = 1.0*mm;
  const G4double sipmCenterZ = 146.0*mm;
  G4Box* sipmSolid =
    new G4Box("SiPM_solid", detectorXY/2.0, detectorXY/2.0, sipmThickness/2.0);
  G4LogicalVolume* sipmLogical =
    new G4LogicalVolume(sipmSolid, fSiPMMaterial, "SiPM_log");
  new G4PVPlacement(0, G4ThreeVector(0, 0, sipmCenterZ), "SiPM_phys",
                    sipmLogical, worldPhysical, false, 0);

  const G4double collimatorXY = 64.0*mm;
  const G4double collimatorLength = 35.0*mm;
  const G4double collimatorCenterZ = 117.5*mm;
  const G4double holeSize = 1.5*mm;
  const G4double septumThickness = 0.2*mm;
  const G4int halfGrid = 18;
  const G4double pitch = 1.7*mm;
  const G4int holeCount = 2*halfGrid + 1;
  const G4double activeXY = holeCount*pitch;
  const G4double borderThickness = (collimatorXY - activeXY)/2.0;

  G4LogicalVolume* collimatorLogical =
    new G4LogicalVolume(
      new G4Box("Collimator_envelope",
                collimatorXY/2.0, collimatorXY/2.0, collimatorLength/2.0),
      fWorldMaterial, "Collimator_envelope_log");
  new G4PVPlacement(0, G4ThreeVector(0, 0, collimatorCenterZ), "Collimator_phys",
                    collimatorLogical, worldPhysical, false, 0);

  G4LogicalVolume* borderSideLogical =
    new G4LogicalVolume(
      new G4Box("Collimator_border_side",
                borderThickness/2.0, collimatorXY/2.0, collimatorLength/2.0),
      fLeadMaterial, "Collimator_border_side_log");
  G4LogicalVolume* borderTopBottomLogical =
    new G4LogicalVolume(
      new G4Box("Collimator_border_top_bottom",
                activeXY/2.0, borderThickness/2.0, collimatorLength/2.0),
      fLeadMaterial, "Collimator_border_top_bottom_log");
  G4LogicalVolume* outerVerticalSeptumLogical =
    new G4LogicalVolume(
      new G4Box("Collimator_outer_vertical_septum",
                septumThickness/4.0, activeXY/2.0, collimatorLength/2.0),
      fLeadMaterial, "Collimator_outer_vertical_septum_log");
  G4LogicalVolume* innerVerticalSeptumLogical =
    new G4LogicalVolume(
      new G4Box("Collimator_inner_vertical_septum",
                septumThickness/2.0, activeXY/2.0, collimatorLength/2.0),
      fLeadMaterial, "Collimator_inner_vertical_septum_log");
  G4LogicalVolume* outerHorizontalSeptumLogical =
    new G4LogicalVolume(
      new G4Box("Collimator_outer_horizontal_septum",
                holeSize/2.0, septumThickness/4.0, collimatorLength/2.0),
      fLeadMaterial, "Collimator_outer_horizontal_septum_log");
  G4LogicalVolume* innerHorizontalSeptumLogical =
    new G4LogicalVolume(
      new G4Box("Collimator_inner_horizontal_septum",
                holeSize/2.0, septumThickness/2.0, collimatorLength/2.0),
      fLeadMaterial, "Collimator_inner_horizontal_septum_log");

  G4int copyNo = 0;
  const G4double activeEdge = activeXY/2.0;
  const G4double borderCenter = collimatorXY/2.0 - borderThickness/2.0;
  new G4PVPlacement(0, G4ThreeVector(-borderCenter, 0, 0),
                    borderSideLogical, "Collimator_border_side_phys",
                    collimatorLogical, false, copyNo++);
  new G4PVPlacement(0, G4ThreeVector(borderCenter, 0, 0),
                    borderSideLogical, "Collimator_border_side_phys",
                    collimatorLogical, false, copyNo++);
  new G4PVPlacement(0, G4ThreeVector(0, -borderCenter, 0),
                    borderTopBottomLogical, "Collimator_border_top_bottom_phys",
                    collimatorLogical, false, copyNo++);
  new G4PVPlacement(0, G4ThreeVector(0, borderCenter, 0),
                    borderTopBottomLogical, "Collimator_border_top_bottom_phys",
                    collimatorLogical, false, copyNo++);

  new G4PVPlacement(0, G4ThreeVector(-activeEdge + septumThickness/4.0, 0, 0),
                    outerVerticalSeptumLogical,
                    "Collimator_outer_vertical_septum_phys",
                    collimatorLogical, false, copyNo++);
  new G4PVPlacement(0, G4ThreeVector(activeEdge - septumThickness/4.0, 0, 0),
                    outerVerticalSeptumLogical,
                    "Collimator_outer_vertical_septum_phys",
                    collimatorLogical, false, copyNo++);
  for (G4int ix = -halfGrid; ix < halfGrid; ++ix) {
    const G4double x = (ix + 0.5)*pitch;
    new G4PVPlacement(0, G4ThreeVector(x, 0, 0),
                      innerVerticalSeptumLogical,
                      "Collimator_inner_vertical_septum_phys",
                      collimatorLogical, false, copyNo++);
  }

  for (G4int ix = -halfGrid; ix <= halfGrid; ++ix) {
    const G4double x = ix*pitch;
    new G4PVPlacement(0, G4ThreeVector(x, -activeEdge + septumThickness/4.0, 0),
                      outerHorizontalSeptumLogical,
                      "Collimator_outer_horizontal_septum_phys",
                      collimatorLogical, false, copyNo++);
    new G4PVPlacement(0, G4ThreeVector(x, activeEdge - septumThickness/4.0, 0),
                      outerHorizontalSeptumLogical,
                      "Collimator_outer_horizontal_septum_phys",
                      collimatorLogical, false, copyNo++);

    for (G4int iy = -halfGrid; iy < halfGrid; ++iy) {
      const G4double y = (iy + 0.5)*pitch;
      new G4PVPlacement(0, G4ThreeVector(x, y, 0),
                        innerHorizontalSeptumLogical,
                        "Collimator_inner_horizontal_septum_phys",
                        collimatorLogical, false, copyNo++);
    }
  }

  worldLogical->SetVisAttributes(G4VisAttributes::Invisible);
  fLYSOLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.0, 0.7, 1.0, 0.4)));
  gelLogical->SetVisAttributes(new G4VisAttributes(G4Colour(1.0, 1.0, 1.0, 0.3)));
  sipmLogical->SetVisAttributes(new G4VisAttributes(G4Colour(0.1, 0.1, 0.1)));
  collimatorLogical->SetVisAttributes(G4VisAttributes::Invisible);
  G4VisAttributes* leadVis = new G4VisAttributes(G4Colour(0.45, 0.45, 0.45));
  borderSideLogical->SetVisAttributes(leadVis);
  borderTopBottomLogical->SetVisAttributes(leadVis);
  outerVerticalSeptumLogical->SetVisAttributes(leadVis);
  innerVerticalSeptumLogical->SetVisAttributes(leadVis);
  outerHorizontalSeptumLogical->SetVisAttributes(leadVis);
  innerHorizontalSeptumLogical->SetVisAttributes(leadVis);

  return worldPhysical;
}

void SpectDetectorConstruction::ConstructSDandField()
{
  SpectSensitiveDetector* lysoSD = new SpectSensitiveDetector("/SPECT/LYSOSD");
  G4SDManager::GetSDMpointer()->AddNewDetector(lysoSD);
  if (fLYSOLogical) {
    SetSensitiveDetector(fLYSOLogical, lysoSD);
  }
}
