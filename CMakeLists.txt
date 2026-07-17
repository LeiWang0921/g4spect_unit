cmake_minimum_required(VERSION 3.5 FATAL_ERROR)
project(g4spect_unit)

option(WITH_GEANT4_UIVIS "Build with Geant4 UI and Vis drivers" ON)
if(WITH_GEANT4_UIVIS)
  find_package(Geant4 REQUIRED ui_all vis_all)
else()
  find_package(Geant4 REQUIRED)
endif()

include(${Geant4_USE_FILE})

include_directories(${PROJECT_SOURCE_DIR}/include ${Geant4_INCLUDE_DIR})
# src/SpectDicomPhantom.cc and src/SpectMirdHumanPhantom.cc are included by the src/*.cc source glob.
file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(G4SPECT G4SPECT.cc ${sources} ${headers})
target_link_libraries(G4SPECT ${Geant4_LIBRARIES})

add_custom_target(g4spect_unit DEPENDS G4SPECT)
install(TARGETS G4SPECT DESTINATION bin)
