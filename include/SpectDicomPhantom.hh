#ifndef SpectDicomPhantom_h
#define SpectDicomPhantom_h 1

#include "globals.hh"

class G4LogicalVolume;

class SpectDicomPhantom
{
public:
  SpectDicomPhantom();
  ~SpectDicomPhantom();

  void Construct(G4LogicalVolume* worldLogical);

private:
  G4String ResolveDataPath() const;
};

#endif
