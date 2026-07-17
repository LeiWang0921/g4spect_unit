#include "SpectDicomPhantom.hh"

#include "G4Box.hh"
#include "G4Colour.hh"
#include "G4Exception.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVParameterised.hh"
#include "G4PVPlacement.hh"
#include "G4PhantomParameterisation.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4VisAttributes.hh"
#include "G4VPhysicalVolume.hh"

#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace
{
struct DicomSlice
{
  std::vector<G4String> materialNames;
  G4int nx;
  G4int ny;
  G4int nz;
  G4double minX;
  G4double maxX;
  G4double minY;
  G4double maxY;
  G4double minZ;
  G4double maxZ;
  std::vector<G4int> materialIds;
};

void Fail(const G4String& message)
{
  G4Exception("SpectDicomPhantom", "G4SPECT_DICOM", FatalException, message);
}

G4bool EnvFlagEnabled(const char* name)
{
  const char* value = std::getenv(name);
  if (!value || value[0] == '\0') {
    return false;
  }
  G4String text(value);
  return text != "0" && text != "false" && text != "FALSE";
}

G4String JoinPath(const G4String& directory, const G4String& file)
{
  if (directory.empty()) {
    return file;
  }
  const char last = directory[directory.size() - 1];
  if (last == '/' || last == '\\') {
    return directory + file;
  }
  return directory + "/" + file;
}

std::vector<G4String> SplitFiles(const G4String& files)
{
  std::vector<G4String> result;
  std::stringstream stream(files);
  std::string item;
  while (std::getline(stream, item, ',')) {
    if (!item.empty()) {
      result.push_back(item);
    }
  }
  return result;
}

DicomSlice ReadSlice(const G4String& fileName)
{
  std::ifstream input(fileName.c_str());
  if (!input) {
    Fail("Cannot open DICOM phantom slice: " + fileName);
  }

  DicomSlice slice;
  G4int nMaterials = 0;
  input >> nMaterials;
  if (!input || nMaterials <= 0) {
    Fail("Invalid material table in DICOM phantom slice: " + fileName);
  }

  slice.materialNames.resize(nMaterials);
  for (G4int i = 0; i < nMaterials; ++i) {
    G4int materialId = 0;
    G4String materialName;
    input >> materialId >> materialName;
    if (!input || materialId < 0 || materialId >= nMaterials) {
      Fail("Invalid material entry in DICOM phantom slice: " + fileName);
    }
    slice.materialNames[materialId] = materialName;
  }

  input >> slice.nx >> slice.ny >> slice.nz;
  input >> slice.minX >> slice.maxX;
  input >> slice.minY >> slice.maxY;
  input >> slice.minZ >> slice.maxZ;
  if (!input || slice.nx <= 0 || slice.ny <= 0 || slice.nz <= 0) {
    Fail("Invalid voxel dimensions in DICOM phantom slice: " + fileName);
  }

  const G4int nVoxels = slice.nx * slice.ny * slice.nz;
  slice.materialIds.resize(nVoxels);
  for (G4int i = 0; i < nVoxels; ++i) {
    input >> slice.materialIds[i];
    if (!input) {
      Fail("Missing material indices in DICOM phantom slice: " + fileName);
    }
  }

  return slice;
}

G4Material* FindMaterialWithFallback(const G4String& materialName)
{
  G4NistManager* nist = G4NistManager::Instance();
  std::vector<G4String> candidates;

  if (materialName.find("G4_") == 0) {
    candidates.push_back(materialName);
  } else if (materialName == "Air") {
    candidates.push_back("G4_AIR");
  } else if (materialName == "LungInhale" || materialName == "LungExhale") {
    candidates.push_back("G4_LUNG_ICRP");
    candidates.push_back("G4_WATER");
  } else if (materialName == "AdiposeTissue") {
    candidates.push_back("G4_ADIPOSE_TISSUE_ICRP");
    candidates.push_back("G4_WATER");
  } else if (materialName == "Breast") {
    candidates.push_back("G4_WATER");
  } else if (materialName == "Water") {
    candidates.push_back("G4_WATER");
  } else if (materialName == "Muscle") {
    candidates.push_back("G4_MUSCLE_WITH_SUCROSE");
    candidates.push_back("G4_MUSCLE_SKELETAL_ICRP");
    candidates.push_back("G4_WATER");
  } else if (materialName == "Liver") {
    candidates.push_back("G4_WATER");
  } else if (materialName == "TrabecularBone") {
    candidates.push_back("G4_BONE_COMPACT_ICRU");
    candidates.push_back("G4_BONE_CORTICAL_ICRP");
  } else if (materialName == "DenseBone") {
    candidates.push_back("G4_BONE_CORTICAL_ICRP");
    candidates.push_back("G4_BONE_COMPACT_ICRU");
  } else {
    candidates.push_back(materialName);
    candidates.push_back("G4_WATER");
  }

  for (std::vector<G4String>::const_iterator it = candidates.begin();
       it != candidates.end(); ++it) {
    G4Material* material = nist->FindOrBuildMaterial(*it, false);
    if (material) {
      return material;
    }
  }

  Fail("Cannot map DICOM material to a Geant4 material: " + materialName);
  return 0;
}
}

SpectDicomPhantom::SpectDicomPhantom()
{
}

SpectDicomPhantom::~SpectDicomPhantom()
{
}

G4String SpectDicomPhantom::ResolveDataPath() const
{
  const char* path = std::getenv("G4SPECT_DICOM_PATH");
  if (path && path[0] != '\0') {
    return G4String(path);
  }
  return "/opt/geant4_10.5/examples/extended/medical/DICOM";
}

void SpectDicomPhantom::Construct(G4LogicalVolume* worldLogical)
{
  const G4String dataPath = ResolveDataPath();
  std::vector<G4String> sliceFiles;
  const char* fileList = std::getenv("G4SPECT_DICOM_FILES");
  if (fileList && fileList[0] != '\0') {
    sliceFiles = SplitFiles(fileList);
  } else {
    sliceFiles.push_back("1.g4dcm");
    sliceFiles.push_back("2.g4dcm");
    sliceFiles.push_back("3.g4dcm");
  }

  std::vector<DicomSlice> slices;
  for (std::vector<G4String>::const_iterator it = sliceFiles.begin();
       it != sliceFiles.end(); ++it) {
    slices.push_back(ReadSlice(JoinPath(dataPath, *it)));
  }
  if (slices.empty()) {
    Fail("No DICOM phantom slices were provided.");
  }

  std::sort(slices.begin(), slices.end(),
            [](const DicomSlice& a, const DicomSlice& b) {
              return a.minZ < b.minZ;
            });

  const DicomSlice& first = slices.front();
  std::vector<G4String> materialNames = first.materialNames;
  G4int nX = first.nx;
  G4int nY = first.ny;
  G4int nZ = 0;
  G4double minX = first.minX;
  G4double maxX = first.maxX;
  G4double minY = first.minY;
  G4double maxY = first.maxY;
  G4double minZ = slices.front().minZ;
  G4double maxZ = slices.front().maxZ;
  std::vector<G4int> mergedMaterialIds;

  for (std::vector<DicomSlice>::const_iterator it = slices.begin();
       it != slices.end(); ++it) {
    if (it->nx != nX || it->ny != nY || it->minX != minX || it->maxX != maxX ||
        it->minY != minY || it->maxY != maxY ||
        it->materialNames.size() != materialNames.size()) {
      Fail("DICOM slices use inconsistent dimensions or material tables.");
    }
    nZ += it->nz;
    minZ = std::min(minZ, it->minZ);
    maxZ = std::max(maxZ, it->maxZ);
    mergedMaterialIds.insert(mergedMaterialIds.end(),
                             it->materialIds.begin(), it->materialIds.end());
  }

  std::vector<G4Material*> materials;
  for (std::vector<G4String>::const_iterator it = materialNames.begin();
       it != materialNames.end(); ++it) {
    materials.push_back(FindMaterialWithFallback(*it));
  }

  const G4int nVoxels = nX * nY * nZ;
  if (static_cast<G4int>(mergedMaterialIds.size()) != nVoxels) {
    Fail("Merged DICOM phantom voxel count is inconsistent.");
  }

  size_t* materialIndices = new size_t[nVoxels];
  for (G4int i = 0; i < nVoxels; ++i) {
    if (mergedMaterialIds[i] < 0 ||
        mergedMaterialIds[i] >= static_cast<G4int>(materials.size())) {
      Fail("DICOM phantom contains a material index outside the material table.");
    }
    materialIndices[i] = static_cast<size_t>(mergedMaterialIds[i]);
  }

  const G4double halfX = (maxX - minX) * 0.5 * mm;
  const G4double halfY = (maxY - minY) * 0.5 * mm;
  const G4double halfZ = (maxZ - minZ) * 0.5 * mm;
  const G4double voxelHalfX = halfX / nX;
  const G4double voxelHalfY = halfY / nY;
  const G4double voxelHalfZ = halfZ / nZ;

  G4Box* containerSolid =
    new G4Box("DICOM_PhantomContainer_solid", halfX, halfY, halfZ);
  G4LogicalVolume* containerLogical =
    new G4LogicalVolume(containerSolid, materials[0],
                        "DICOM_PhantomContainer_log");
  new G4PVPlacement(0, G4ThreeVector(), containerLogical,
                    "DICOM_PhantomContainer_phys", worldLogical, false, 0);

  G4Box* voxelSolid =
    new G4Box("DICOM_PhantomVoxel_solid", voxelHalfX, voxelHalfY, voxelHalfZ);
  G4LogicalVolume* voxelLogical =
    new G4LogicalVolume(voxelSolid, materials[0], "DICOM_PhantomVoxel_log");

  G4PhantomParameterisation* param = new G4PhantomParameterisation();
  param->SetVoxelDimensions(voxelHalfX, voxelHalfY, voxelHalfZ);
  param->SetNoVoxel(nX, nY, nZ);
  param->SetMaterials(materials);
  param->SetMaterialIndices(materialIndices);
  param->BuildContainerSolid(containerSolid);
  param->CheckVoxelsFillContainer(containerSolid->GetXHalfLength(),
                                  containerSolid->GetYHalfLength(),
                                  containerSolid->GetZHalfLength());

  G4PVParameterised* phantomPhysical =
    new G4PVParameterised("DICOM_PhantomVoxel_phys", voxelLogical,
                          containerLogical, kXAxis, nVoxels, param);
  phantomPhysical->SetRegularStructureId(1);

  G4VisAttributes* containerVis =
    new G4VisAttributes(G4Colour(0.75, 0.55, 0.35, 0.12));
  containerVis->SetVisibility(true);
  containerVis->SetForceSolid(true);
  containerLogical->SetVisAttributes(containerVis);

  G4VisAttributes* voxelVis =
    new G4VisAttributes(G4Colour(0.85, 0.65, 0.45, 0.18));
  const G4bool showDicomVoxels = EnvFlagEnabled("G4SPECT_SHOW_DICOM_VOXELS");
  voxelVis->SetVisibility(showDicomVoxels);
  voxelVis->SetForceSolid(showDicomVoxels);
  voxelLogical->SetVisAttributes(voxelVis);
}
