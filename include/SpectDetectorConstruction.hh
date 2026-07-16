#ifndef SpectDetectorConstruction_h
#define SpectDetectorConstruction_h 1

#include "G4VUserDetectorConstruction.hh"

class G4LogicalVolume;
class G4Material;
class G4VPhysicalVolume;

class SpectDetectorConstruction : public G4VUserDetectorConstruction
{
public:
  SpectDetectorConstruction();
  virtual ~SpectDetectorConstruction();

  virtual G4VPhysicalVolume* Construct();
  virtual void ConstructSDandField();

private:
  void DefineMaterials();
  G4Material* BuildLYSO();
  G4Material* BuildOpticalGel();

  G4LogicalVolume* fLYSOLogical;
  G4Material* fWorldMaterial;
  G4Material* fLeadMaterial;
  G4Material* fLYSOMaterial;
  G4Material* fGelMaterial;
  G4Material* fSiPMMaterial;
};

#endif
