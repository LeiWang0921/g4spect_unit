#include "SpectMirdHumanPhantom.hh"

#include "G4Colour.hh"
#include "G4Ellipsoid.hh"
#include "G4EllipticalTube.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4RotationMatrix.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4VisAttributes.hh"

namespace
{
G4RotationMatrix* RotateTubeAlongY()
{
  G4RotationMatrix* rotation = new G4RotationMatrix();
  rotation->rotateX(90.0*deg);
  return rotation;
}

void ApplyBodyVis(G4LogicalVolume* logical)
{
  G4VisAttributes* vis =
    new G4VisAttributes(G4Colour(0.86, 0.62, 0.42, 0.28));
  vis->SetVisibility(true);
  vis->SetForceSolid(true);
  logical->SetVisAttributes(vis);
}
}

SpectMirdHumanPhantom::SpectMirdHumanPhantom()
{
}

SpectMirdHumanPhantom::~SpectMirdHumanPhantom()
{
}

G4Material* SpectMirdHumanPhantom::BuildBodyMaterial()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Material* material = nist->FindOrBuildMaterial("G4_TISSUE_SOFT_ICRP", false);
  if (!material) {
    material = nist->FindOrBuildMaterial("G4_WATER");
  }
  return material;
}

void SpectMirdHumanPhantom::Construct(G4LogicalVolume* worldLogical)
{
  G4Material* bodyMaterial = BuildBodyMaterial();

  G4LogicalVolume* trunkLogical =
    new G4LogicalVolume(
      new G4EllipticalTube("HumanPhantom_Trunk_solid",
                           20.0*cm, 10.0*cm, 35.0*cm),
      bodyMaterial, "HumanPhantom_Trunk_log");
  new G4PVPlacement(RotateTubeAlongY(), G4ThreeVector(0, 0, 0),
                    trunkLogical, "HumanPhantom_Trunk_phys",
                    worldLogical, false, 0);
  ApplyBodyVis(trunkLogical);

  G4LogicalVolume* headLogical =
    new G4LogicalVolume(
      new G4Ellipsoid("HumanPhantom_Head_solid",
                      8.0*cm, 10.0*cm, 10.0*cm),
      bodyMaterial, "HumanPhantom_Head_log");
  new G4PVPlacement(0, G4ThreeVector(0, 47.0*cm, 0),
                    headLogical, "HumanPhantom_Head_phys",
                    worldLogical, false, 0);
  ApplyBodyVis(headLogical);

  G4LogicalVolume* armLogical =
    new G4LogicalVolume(
      new G4EllipticalTube("HumanPhantom_Arm_solid",
                           4.0*cm, 5.0*cm, 32.0*cm),
      bodyMaterial, "HumanPhantom_Arm_log");
  new G4PVPlacement(RotateTubeAlongY(), G4ThreeVector(-25.0*cm, -2.0*cm, 0),
                    armLogical, "HumanPhantom_LeftArm_phys",
                    worldLogical, false, 0);
  new G4PVPlacement(RotateTubeAlongY(), G4ThreeVector(25.0*cm, -2.0*cm, 0),
                    armLogical, "HumanPhantom_RightArm_phys",
                    worldLogical, false, 1);
  ApplyBodyVis(armLogical);

  G4LogicalVolume* legLogical =
    new G4LogicalVolume(
      new G4EllipticalTube("HumanPhantom_Leg_solid",
                           6.0*cm, 7.0*cm, 40.0*cm),
      bodyMaterial, "HumanPhantom_Leg_log");
  new G4PVPlacement(RotateTubeAlongY(), G4ThreeVector(-7.0*cm, -75.0*cm, 0),
                    legLogical, "HumanPhantom_LeftLeg_phys",
                    worldLogical, false, 0);
  new G4PVPlacement(RotateTubeAlongY(), G4ThreeVector(7.0*cm, -75.0*cm, 0),
                    legLogical, "HumanPhantom_RightLeg_phys",
                    worldLogical, false, 1);
  ApplyBodyVis(legLogical);
}
