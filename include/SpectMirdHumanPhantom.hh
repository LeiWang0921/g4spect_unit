#ifndef SpectMirdHumanPhantom_h
#define SpectMirdHumanPhantom_h 1

#include "globals.hh"

class G4LogicalVolume;
class G4Material;

class SpectMirdHumanPhantom
{
public:
  SpectMirdHumanPhantom();
  ~SpectMirdHumanPhantom();

  void Construct(G4LogicalVolume* worldLogical);

private:
  G4Material* BuildBodyMaterial();
};

#endif
