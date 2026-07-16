# G4SPECT 运行说明

本文说明远端 `g4spect_unit` Geant4 原型如何编译和运行、它模拟什么物理过程，以及运行后会得到什么输出。

## 项目位置

远端项目目录：

```bash
/RHEL7/home/lwang2/g4spect_unit
```

编译后的主程序：

```bash
/RHEL7/home/lwang2/g4spect_unit/build/G4SPECT
```

## 这个程序做什么

`g4spect_unit` 是当前 SPECT 探测器单元的最小 Geant4 原型。它模拟 Tc-99m gamma 光子从源出发，经过 Pb 平行孔准直器，进入 LSO 闪烁晶体后的输运和能量沉积。

当前 Geant4 阶段不产生光学光子。它只记录 LSO 中的能量沉积和粒子 step 信息。后续计划是把这些 LSO 能量沉积结果交给 Chroma，由 Chroma 负责闪烁光子的产生、传播、界面光学和 SiPM 探测。

当前几何顺序沿 `+z` 方向为：

```text
Tc-99m gamma 源
  -> Pb 平行孔准直器
  -> LSO 晶体
  -> optical gel
  -> SiPM slab
```

## 几何和材料

几何定义在：

```bash
src/SpectDetectorConstruction.cc
```

当前材料：

- World：`G4_AIR`
- 准直器：`G4_Pb`
- LSO：自定义 `LSO`，密度 `7.40 g/cm3`
- 光学胶：自定义 `OpticalGel`，密度 `1.03 g/cm3`
- SiPM：`G4_Si`

当前尺寸：

- 探测器横向尺寸：`32 mm x 32 mm`
- LSO：`32 mm x 32 mm x 10 mm`，中心在 `z = 0 mm`
- 光学胶：`32 mm x 32 mm x 0.5 mm`，中心在 `z = 5.25 mm`
- SiPM：`32 mm x 32 mm x 1 mm`，中心在 `z = 6.0 mm`
- 准直器：`32 mm x 32 mm x 25 mm`，中心在 `z = -19.0 mm`
- 准直器孔阵列：`9 x 9` 个方孔
- 单孔孔径：`2.4 mm x 2.4 mm`
- 孔中心距：`3.2 mm`
- septum 厚度：`0.8 mm`

准直器孔洞是从 Pb 块中 subtract 出来的。因此孔洞本身不是一个单独的实体材料，而是 world air。

## Geant4 直接几何导出

当前首选几何检查方式是 Geant4 自带 `VRML2FILE` 从真实
`SpectDetectorConstruction.cc` geometry 导出的 3D 文件，不是手写 HTML 复刻。
这里的 `.wrl` 是 Geant4 直接导出的原始查看文件；`.obj/.mtl` 只是由 `.wrl`
转换得到的本地查看副本，不是新的几何定义。

从零开始做一次带轨迹的几何导出，分三步：

1. 在服务器上准备环境和可执行文件。
2. 运行 `export_geometry_tracks_ShowAllBeam.mac` 或
   `export_geometry_tracks_ShowDetectedBeam.mac`，生成 `.wrl` 并转换成 `.obj/.mtl`。
3. 把生成的 3D 文件拷贝回本地，用 3D 查看器打开。

### 0. 服务器准备

从本地 PowerShell 登录服务器：

```powershell
ssh lwang2@phaarmonster.triumf.ca
```

在服务器上进入项目、加载 Geant4 环境、确认 build 目录和输出目录存在：

```bash
cd /RHEL7/home/lwang2/g4spect_unit
source /opt/geant4_10.5/install/bin/geant4.sh
mkdir -p build output geometry_exports
```

如果 `build/G4SPECT` 还不存在，先编译：

```bash
cd /RHEL7/home/lwang2/g4spect_unit/build
cmake -DGeant4_DIR=/opt/geant4_10.5/install/lib/Geant4-10.5.1 ..
cmake --build . -j2
```

之后所有导出命令都从服务器的 build 目录运行：

```bash
cd /RHEL7/home/lwang2/g4spect_unit/build
```

`tools/vrml_to_obj.py` 已经内置默认本地复制目标：

```text
Leiwa@10.90.70.110:/E:/SPECT/g4spect_unit/geometry_exports/
```

因此在服务器上无参数运行：

```bash
python3 ../tools/vrml_to_obj.py
```

会在转换完成后自动尝试把 `.wrl/.obj/.mtl` 和 Blender 导入脚本复制到本地
`E:\SPECT\g4spect_unit\geometry_exports\`，文件名保持为
`spect_geometry_tracks.wrl/.obj/.mtl` 和 `import_tracks_blender.py`。

前提是服务器能通过 `scp` 访问本地电脑。当前本地 IP 是 `10.90.70.110`；如果本地没有开启
Windows SSH server，或者防火墙不允许服务器访问本地 22 端口，自动复制会失败，但服务器上的
`geometry_exports/spect_geometry_tracks.*` 仍然已经生成。需要临时覆盖默认目标时，可以使用
`G4SPECT_COPY_TO` 或 `--copy-to`。

`G4VRMLFILE_MAX_FILE_NUM=1` 是当前推荐的 VRML 导出方式。Geant4 10.5 的
`VRML2FILE` 驱动会按 `g4_00.wrl`、`g4_01.wrl`、…… 自动寻找文件名，不能在 macro
中直接指定任意输出文件名。把最大文件数设为 `1` 后，它会固定使用并覆盖
`build/g4_00.wrl`，避免每次运行都产生一个新的 `g4_XX.wrl`。

### 1. 运行 ShowAllBeam

`export_geometry_tracks_ShowAllBeam.mac` 用 directed beam 跑前 5 个 generated event。
它会导出探测器几何、源位置坐标轴和这 5 个 event 的轨迹。

在服务器上运行：

```bash
cd /RHEL7/home/lwang2/g4spect_unit/build
source /opt/geant4_10.5/install/bin/geant4.sh
G4VRMLFILE_MAX_FILE_NUM=1 ./G4SPECT ../mac/export_geometry_tracks_ShowAllBeam.mac

python3 ../tools/vrml_to_obj.py
ls -lh ../geometry_exports/spect_geometry_tracks.wrl \
       ../geometry_exports/spect_geometry_tracks.obj \
       ../geometry_exports/spect_geometry_tracks.mtl
```

运行完成后，服务器上会得到：

```text
/RHEL7/home/lwang2/g4spect_unit/geometry_exports/spect_geometry_tracks.wrl
/RHEL7/home/lwang2/g4spect_unit/geometry_exports/spect_geometry_tracks.obj
/RHEL7/home/lwang2/g4spect_unit/geometry_exports/spect_geometry_tracks.mtl
```

`python3 ../tools/vrml_to_obj.py` 无参数运行时，会优先读取
`build/g4_00.wrl`，复制成 `geometry_exports/spect_geometry_tracks.wrl`，
并生成同名的 `.obj/.mtl`。如果 `build/g4_00.wrl` 不存在，脚本才会回退到
`build/` 目录中最新的 `*.wrl`。随后脚本会自动把 3D 文件和 Blender 导入脚本复制到内置的本地目标目录。

如果之后还要运行 `ShowDetectedBeam`，但想保留 `ShowAllBeam` 的结果，先在服务器上改名保存：

```bash
cd /RHEL7/home/lwang2/g4spect_unit
cp geometry_exports/spect_geometry_tracks.wrl geometry_exports/spect_geometry_tracks_ShowAllBeam.wrl
cp geometry_exports/spect_geometry_tracks.obj geometry_exports/spect_geometry_tracks_ShowAllBeam.obj
cp geometry_exports/spect_geometry_tracks.mtl geometry_exports/spect_geometry_tracks_ShowAllBeam.mtl
```

### 2. 运行 ShowDetectedBeam

`export_geometry_tracks_ShowDetectedBeam.mac` 使用 isotropic source，并用 Geant4 的
`encounteredVolumeFilter` 按 `LSO_phys` 过滤轨迹。它运行 `/run/beamOn 10000`，
突出显示遇到 LSO 的轨迹。

在服务器上运行：

```bash
cd /RHEL7/home/lwang2/g4spect_unit/build
source /opt/geant4_10.5/install/bin/geant4.sh
G4VRMLFILE_MAX_FILE_NUM=1 ./G4SPECT ../mac/export_geometry_tracks_ShowDetectedBeam.mac

python3 ../tools/vrml_to_obj.py
ls -lh ../geometry_exports/spect_geometry_tracks.wrl \
       ../geometry_exports/spect_geometry_tracks.obj \
       ../geometry_exports/spect_geometry_tracks.mtl
```

这一步会覆盖同一套 `geometry_exports/spect_geometry_tracks.*` 文件。如果想保留
`ShowDetectedBeam` 的结果，也可以改名保存：

```bash
cd /RHEL7/home/lwang2/g4spect_unit
cp geometry_exports/spect_geometry_tracks.wrl geometry_exports/spect_geometry_tracks_ShowDetectedBeam.wrl
cp geometry_exports/spect_geometry_tracks.obj geometry_exports/spect_geometry_tracks_ShowDetectedBeam.obj
cp geometry_exports/spect_geometry_tracks.mtl geometry_exports/spect_geometry_tracks_ShowDetectedBeam.mtl
```

### 3. 拷贝到本地并打开 3D 视图

正常情况下，这一步会在 `python3 ../tools/vrml_to_obj.py` 成功后自动完成。本地会得到：

```text
E:\SPECT\g4spect_unit\geometry_exports\spect_geometry_tracks.wrl
E:\SPECT\g4spect_unit\geometry_exports\spect_geometry_tracks.obj
E:\SPECT\g4spect_unit\geometry_exports\spect_geometry_tracks.mtl
E:\SPECT\g4spect_unit\geometry_exports\import_tracks_blender.py
```

如果没有配置服务器主动复制，仍然可以在本地 PowerShell 中手动拉取最近一次运行的默认文件：

```powershell
New-Item -ItemType Directory -Force -Path 'g4spect_unit\geometry_exports' | Out-Null

C:\Windows\System32\OpenSSH\scp.exe `
  lwang2@phaarmonster.triumf.ca:/RHEL7/home/lwang2/g4spect_unit/geometry_exports/spect_geometry_tracks.wrl `
  lwang2@phaarmonster.triumf.ca:/RHEL7/home/lwang2/g4spect_unit/geometry_exports/spect_geometry_tracks.obj `
  lwang2@phaarmonster.triumf.ca:/RHEL7/home/lwang2/g4spect_unit/geometry_exports/spect_geometry_tracks.mtl `
  lwang2@phaarmonster.triumf.ca:/RHEL7/home/lwang2/g4spect_unit/geometry_exports/import_tracks_blender.py `
  g4spect_unit\geometry_exports\

Get-Item g4spect_unit\geometry_exports\spect_geometry_tracks.* |
  Select-Object Name,Length,LastWriteTime
Get-Item g4spect_unit\geometry_exports\import_tracks_blender.py |
  Select-Object Name,Length,LastWriteTime
```

如果服务器上已经改名保存了两个版本，按需要拷贝对应文件，例如：

```powershell
C:\Windows\System32\OpenSSH\scp.exe `
  lwang2@phaarmonster.triumf.ca:/RHEL7/home/lwang2/g4spect_unit/geometry_exports/spect_geometry_tracks_ShowAllBeam.* `
  lwang2@phaarmonster.triumf.ca:/RHEL7/home/lwang2/g4spect_unit/geometry_exports/spect_geometry_tracks_ShowDetectedBeam.* `
  g4spect_unit\geometry_exports\
```

打开 3D 视图时优先在 Blender 中运行 `import_tracks_blender.py`，不要直接用
`File > Open` 打开 OBJ。`File > Open` 是打开 `.blend` 文件用的，不会正确导入
OBJ。`import_tracks_blender.py` 会导入同目录下的 `spect_geometry_tracks.obj`，
并把对象整理成 collection。

Blender 中推荐操作：

1. 打开 Blender，最好从新场景开始；如果已经导入过旧版本，先删除旧的
   `spect_geometry_tracks` collection。
2. 进入 `Scripting` workspace。
3. 在 Text Editor 中打开：

   ```text
   E:\SPECT\g4spect_unit\geometry_exports\import_tracks_blender.py
   ```

4. 点击 `Run Script`。脚本会自动导入同目录下的 `spect_geometry_tracks.obj`。

`import_tracks_blender.py` 会优先使用脚本中写入的绝对 OBJ 路径；如果这个路径不存在，
再尝试 Blender Text Editor 中打开脚本的磁盘路径，并从脚本同目录寻找
`spect_geometry_tracks.obj`。因此只要 `import_tracks_blender.py`、
`spect_geometry_tracks.obj` 和 `spect_geometry_tracks.mtl` 在同一个本地目录下，
脚本就应该能找到 OBJ。

导入脚本还会根据 Geant4 VRML 中的 `transparency` 值和 `.mtl` 中的 `d` 值设置
Blender 材质透明度。当前 `LSO_phys` 闪烁体和 `OpticalGel_phys` 光学胶都应该显示为
半透明；如果在 Blender 的 Solid View 里看不明显，切到 Material Preview 或 Rendered View
检查。

也可以手动用 `File > Import > Wavefront (.obj)` 导入
`spect_geometry_tracks.obj`，但这样 collection 层级不会自动整理，只适合快速检查。

当前转换脚本会把 Geant4 的 `POLYLINE` 轨迹转换成独立的 named OBJ objects，并额外生成
细管状 mesh faces，避免 Blender 只导入不可见的 loose line records。默认轨迹管半径是
`0.03 mm`；如果还觉得粗，可以重新转换时指定更小值，例如：

```bash
python3 ../tools/vrml_to_obj.py --line-radius 0.01
```

在 Blender outliner 里：

- `spect_geometry_tracks` 是脚本创建的根 collection。
- `event_001` 到 `event_005` 分别对应 `ShowAllBeam` 的 5 个 generated event。
- `G4AxesModel...` 是 `/vis/scene/add/axes 0 0 -120 10 mm` 生成的源位置坐标轴，不是 gamma 轨迹。
- `gamma_primary_001` 到 `gamma_primary_005` 是 `ShowAllBeam` 的 5 个 primary gamma 轨迹。
- `gamma_secondary_*` 是后续散射/次级 gamma 片段。
- `electron_*` 是电子轨迹。

轨迹颜色约定：

- gamma：yellow
- electron (`e-`)：blue
- positron (`e+`)：cyan

放射源位置用一组小坐标轴标在 `(0, 0, -120 mm)`。普通 Geant4 几何导出不会显示
放射源，因为 GPS source 不是 detector volume。

如果修改了 `src/SpectDetectorConstruction.cc` 中的 detector geometry，例如新增另一个闪烁体、
改变闪烁体材料、移动光学胶或改变某个体积的可视化透明度，通常不需要修改
`tools/vrml_to_obj.py`。重新编译并运行导出 macro 后，Geant4 会把新的 solid、颜色和透明度写入
`.wrl`，转换脚本会按 `.wrl` 内容生成新的 `.obj/.mtl` 和 Blender 导入脚本。只有在需要新增特殊
命名规则、特殊 collection 分组，或者 Geant4 没有在 VRML 中导出的显示属性需要强制覆盖时，才需要
修改 `vrml_to_obj.py`。

如果只想导出不带轨迹的 detector geometry，可以运行
`export_geometry_vrml.mac`，再显式转换：

```bash
cd /RHEL7/home/lwang2/g4spect_unit/build
source /opt/geant4_10.5/install/bin/geant4.sh
G4VRMLFILE_MAX_FILE_NUM=1 ./G4SPECT ../mac/export_geometry_vrml.mac

cd ..
cp build/g4_00.wrl geometry_exports/spect_geometry.wrl
python3 tools/vrml_to_obj.py geometry_exports/spect_geometry.wrl geometry_exports/spect_geometry.obj
```

`visualization/SPECT_geometry_3D.html` 只作为辅助说明图；几何核对优先使用
Geant4 导出的 `.wrl` 文件。如果后续需要更严格的几何交换格式，再考虑 GDML
导出，但任何新增依赖都只能安装到用户个人目录下。

## 物理过程

物理列表定义在：

```bash
src/SpectPhysicsList.cc
```

当前启用：

- 电磁物理：`G4EmLivermorePhysics`
- 衰变：`G4DecayPhysics`
- 放射性衰变：`G4RadioactiveDecayPhysics`
- step limiter：`G4StepLimiterPhysics`
- gamma、电子、正电子的 production cut：`1 um`

初级粒子源使用 Geant4 GPS，即 `G4GeneralParticleSource`。源的位置、角分布、粒子类型和能量由 `mac/` 目录下的 macro 文件控制。

## 编译方法

服务器上已经有可用的 Geant4 10.5：

```bash
cd /RHEL7/home/lwang2/g4spect_unit
source /opt/geant4_10.5/install/bin/geant4.sh
mkdir -p build output
cd build
cmake -DGeant4_DIR=/opt/geant4_10.5/install/lib/Geant4-10.5.1 ..
cmake --build . -j2
```

成功后会生成：

```bash
build/G4SPECT
```
如果要直接运行各向同性点源 macro，确认项目根目录的 `output/` 已存在，然后运行：

```bash
./G4SPECT ../mac/tc99m_point_iso.mac
```

## 快速 smoke test

优先使用 directed beam smoke test 检查程序是否能跑通：

```bash
cd /RHEL7/home/lwang2/g4spect_unit
bash tests/smoke_build_and_run.sh
```

这个脚本会做这些事：

1. 加载 Geant4 环境：

   ```bash
   source /opt/geant4_10.5/install/bin/geant4.sh
   ```

2. 创建 `build/` 和项目根目录的 `output/`。
3. 用 CMake 配置项目。
4. 用 `-j2` 编译 `G4SPECT`。
5. 运行：

   ```bash
   ./G4SPECT ../mac/tc99m_beam_smoke.mac
   ```

`tc99m_beam_smoke.mac` 的设置：

- 粒子：gamma
- 能量：`140.5 keV`
- 源位置：`(0, 0, -120 mm)`
- 方向：`(0, 0, +1)`
- 事件数：`200`
- 输出文件：`output/spect_tc99m_smoke.root`

这个 macro 是定向束流测试，主要用于验证可执行文件、几何、敏感探测器和 ROOT 输出链路是否正常。

## 各向同性点源运行

更接近真实 Tc-99m 点源的 macro 是：

```bash
cd /RHEL7/home/lwang2/g4spect_unit/build
mkdir -p ../output
./G4SPECT ../mac/tc99m_point_iso.mac
```

`tc99m_point_iso.mac` 的设置：

- 粒子：gamma
- 能量：`140.5 keV`
- 源位置：`(0, 0, -120 mm)`
- 角分布：isotropic
- 事件数：`10000`
- 输出文件：`output/spect_tc99m_iso.root`

由于准直器会拒绝绝大多数非准直方向的 gamma，各向同性点源运行的有效命中率会明显低于 directed beam smoke test。这种低命中率可能是物理上合理的，不能直接当成程序错误。

## 源文件职责索引

本节记录当前 `include/` 和 `src/` 中每个源文件的职责。今后只要修改这些源文件中的几何、材料、物理列表、粒子源、敏感探测器、hit 数据结构、ROOT 输出字段或运行入口，就需要同步更新本节和相关运行说明。

### include 头文件

- `include/SpectActionInitialization.hh`

  声明 `SpectActionInitialization`，负责把 Geant4 user actions 注册到 run manager。它定义 `Build()` 和 `BuildForMaster()` 接口，是 primary generator、run action、event action 的装配入口。

- `include/SpectDetectorConstruction.hh`

  声明 `SpectDetectorConstruction`，负责构建 detector geometry、材料和敏感探测器。它保存 LSO logical volume 指针和当前材料指针，并声明 `BuildLSO()`、`BuildOpticalGel()`、`DefineMaterials()`、`Construct()`、`ConstructSDandField()`。

- `include/SpectEventAction.hh`

  声明 `SpectEventAction`，负责在每个 event 结束时读取 LSO hits collection，并把 hit 信息写入 Geant4 analysis ntuple。它缓存 `lsoHitsCollection` 的 collection id。

- `include/SpectHit.hh`

  声明单个 LSO hit 的数据结构 `SpectHit`，包括能量沉积、位置、时间、粒子名、PDG 编码、粒子动能、动量和 track id。文件末尾定义 `SpectHitsCollection`，即 `G4THitsCollection<SpectHit>`。

- `include/SpectPhysicsList.hh`

  声明 `SpectPhysicsList`，负责配置 Geant4 物理列表和 production cuts。当前实现使用 Livermore EM、decay、radioactive decay 和 step limiter。

- `include/SpectPrimaryGeneratorAction.hh`

  声明 `SpectPrimaryGeneratorAction`，负责通过 `G4GeneralParticleSource` 产生 primary vertex。实际源位置、能量和角分布由 macro 文件中的 GPS 命令控制。

- `include/SpectRunAction.hh`

  声明 `SpectRunAction`，负责 run 开始时创建 ROOT 输出和 `tree_chroma` ntuple，run 结束时写入并关闭 ROOT 文件。它还通过 `/spect/output/file` messenger 允许 macro 指定输出文件名。

- `include/SpectSensitiveDetector.hh`

  声明 `SpectSensitiveDetector`，即挂在 LSO logical volume 上的敏感探测器。它负责初始化 hits collection、处理每个 step，并在 event 结束时把 collection 加入 `G4HCofThisEvent`。

### src 实现文件

- `src/SpectActionInitialization.cc`

  实现 user action 注册。worker 线程/普通运行中注册 `SpectPrimaryGeneratorAction`、`SpectRunAction` 和 `SpectEventAction`；master 只注册 `SpectRunAction`。

- `src/SpectDetectorConstruction.cc`

  实现当前所有几何和材料。它创建 world、LSO、optical gel、SiPM 和 Pb parallel-hole collimator；准直器孔洞通过 `G4SubtractionSolid` 从 Pb 块中 subtract 出来。它还把 LSO 设置为敏感体，并设置各部件可视化属性。

- `src/SpectEventAction.cc`

  在 event 结束时遍历 `lsoHitsCollection`，把每个 `SpectHit` 转换成 `tree_chroma` 的一行。它负责单位转换：位置写成 `mm`，时间写成 `ns`，能量和动量相关量写成 `keV`。它还把粒子名映射成当前的数值索引。

- `src/SpectHit.cc`

  实现 `SpectHit` 的构造和析构。构造函数给所有 hit 字段设置默认值，例如 `edep = 0`、`trackID = -1`。

- `src/SpectPhysicsList.cc`

  实现物理列表。当前设置 `defaultCutValue = 1 um`，启用 fluorescence、Auger 和 PIXE，注册 `G4EmLivermorePhysics`、`G4DecayPhysics`、`G4RadioactiveDecayPhysics`、`G4StepLimiterPhysics`，并把 gamma、electron、positron cut 设置为 `1 um`。

- `src/SpectPrimaryGeneratorAction.cc`

  实现 primary generator。构造时创建 `G4GeneralParticleSource`，每个 event 调用 `GeneratePrimaryVertex(event)`。因此源参数主要由运行 macro 决定，而不是硬编码在 C++ 中。

- `src/SpectRunAction.cc`

  实现 ROOT 输出。默认输出文件名为 `spect_output.root`，macro 可以通过 `/spect/output/file` 覆盖。`BeginOfRunAction()` 创建 `tree_chroma` 和所有列；`EndOfRunAction()` 写入并关闭文件。

- `src/SpectSensitiveDetector.cc`

  实现 LSO sensitive detector。每个 event 初始化 `lsoHitsCollection`；对非 optical photon 的 track 记录 first-step hit 和后续 step hit；每个 hit 保存 energy deposition、post-step 位置、local time、粒子信息、动量和 track id。当前 optical photon 会被忽略。

### 入口和构建文件

- `G4SPECT.cc`

  程序入口。它创建 `G4RunManager`，注册 detector construction、physics list 和 action initialization，初始化可视化管理器，并根据命令行参数决定进入 UI session 或执行指定 macro。

- `CMakeLists.txt`

  CMake 构建配置。它查找 Geant4，默认启用 UI/Vis 组件，收集 `src/*.cc` 和 `include/*.hh`，生成 `G4SPECT` 可执行文件，并链接 Geant4 libraries。

## 输出结果

程序使用 Geant4 analysis manager 写 ROOT 文件。

常用输出文件：

```bash
output/spect_tc99m_smoke.root
output/spect_tc99m_iso.root
```

ROOT tree 名称：

```text
tree_chroma
```

`tree_chroma` 记录 LSO 中的 hit/step 信息，当前列包括：

- `event`
- `hits`
- `xpos`
- `ypos`
- `zpos`
- `time`
- `edep`
- `energy`
- `x_momentum`
- `y_momentum`
- `z_momentum`
- `particle_name`
- `PDG`
- `trackID`

每一行代表 LSO sensitive detector 记录到的一条 hit/step 记录。当前实现只记录非 optical photon 的 track；每个 track 在第一步会额外写入一条 `edep = 0` 的 first-hit 记录，用来保存该 track 进入记录流程时的 pre-step 状态，随后每个 Geant4 step 再写入一条常规记录。

字段含义：

| 字段 | 单位 | 含义 |
| --- | --- | --- |
| `event` | 无 | Geant4 event ID。来自 `G4Event::GetEventID()`，用于区分不同 primary event。 |
| `hits` | 无 | 当前 event 内 `lsoHitsCollection` 的条目序号。它是 hit 行索引，不是该 event 的总 hit 数。 |
| `xpos` | `mm` | hit 位置的 x 坐标。first-hit 行使用 pre-step position；常规 step 行使用 post-step position。 |
| `ypos` | `mm` | hit 位置的 y 坐标。规则同 `xpos`。 |
| `zpos` | `mm` | hit 位置的 z 坐标。规则同 `xpos`。 |
| `time` | `ns` | track 在该 step pre-step point 的 local time。first-hit 行也使用 pre-step local time。 |
| `edep` | `keV` | 该 step 的总能量沉积，来自 `G4Step::GetTotalEnergyDeposit()`。first-hit 行固定为 `0`。 |
| `energy` | `keV` | step pre-step point 的粒子动能，来自 `GetKineticEnergy()`。 |
| `x_momentum` | `keV` | 动量 x 分量。first-hit 行使用 pre-step momentum；常规 step 行使用 post-step momentum。Geant4 中动量按能量单位换算写出。 |
| `y_momentum` | `keV` | 动量 y 分量。规则同 `x_momentum`。 |
| `z_momentum` | `keV` | 动量 z 分量。规则同 `x_momentum`。 |
| `particle_name` | 无 | 当前不是字符串，而是由粒子名映射来的数值索引。映射规则见下方列表。 |
| `PDG` | 无 | 粒子的 PDG 编码，来自 `GetPDGEncoding()`。例如 gamma 为 `22`，电子为 `11`。 |
| `trackID` | 无 | Geant4 track ID，用于区分同一 event 内不同 particle track。 |

如何解读这些字段：

- `event = 5506` 表示这是本次 run 中 Geant4 生成的第 `5506` 号 event。Geant4 event ID 从 `0` 开始计数，所以它对应本次 run 的第 `5507` 个 primary event。它不是时间戳，也不是探测器编号。
- `hits = 30` 表示这行是该 event 的 `lsoHitsCollection` 中第 `30` 个条目。这个索引同样从 `0` 开始，所以它是该 event 中第 `31` 条被写出的 LSO hit/step 记录。它不是这个 event 的总 hit 数，也不是第 30 个 SiPM 像素或第 30 个准直孔。
- 同一个 `event` 可以对应多行 ROOT 记录，因为一个 primary gamma 及其产生的次级粒子可能在 LSO 中产生多个 step。分析时通常要按 `event` 分组，再在组内查看 `hits`、`trackID`、`edep` 和位置。
- `xpos/ypos/zpos` 是 Geant4 world coordinate 中的 hit 位置，不是晶体像素编号。当前几何中 LSO 的中心在 `(0, 0, 0)`，横向尺寸是 `32 mm x 32 mm`，所以 LSO 内大多数记录的 `xpos` 和 `ypos` 会落在大约 `-16 mm` 到 `+16 mm` 之间，`zpos` 会落在大约 `-5 mm` 到 `+5 mm` 之间。
- `xpos` 的物理意义是 hit 在 LSO 横向平面中的 x 位置。`xpos = 0 mm` 表示靠近探测器横向中心；`xpos > 0` 和 `xpos < 0` 分别表示中心两侧的两个 x 方向。当前代码没有把 x/y 离散化成 SiPM channel 或 collimator hole index。
- 对于 first-hit 行，`xpos/ypos/zpos` 来自 pre-step position，`edep = 0`，主要用于记录该 track 在开始被 sensitive detector 记录时的位置和动量状态；对于常规 step 行，`xpos/ypos/zpos` 来自 post-step position，`edep` 是该 step 产生的能量沉积。

ROOT 画图时还需要注意：

- ROOT histogram 右上角的 `Entries` 是这张图被填入的条目数。对 `tree_chroma->Draw("event")` 来说，它等于 `tree_chroma` 中被画出的行数，也就是 LSO hit/step 记录数，不是 Geant4 生成的 primary gamma 数。
- 例如 `tc99m_point_iso.mac` 中 `/run/beamOn 10000` 表示 Geant4 生成了 `10000` 个 primary gamma event。由于各向同性源被准直器大量拒绝，绝大多数 event 没有任何 LSO hit，因此不会在 `tree_chroma` 中出现。
- 如果 `event` 图显示 `Entries = 283`，含义是 ROOT 文件里有 `283` 行 LSO hit/step 记录；它不表示只生成了 `283` 个 gamma，也不表示有 `283` 个不同 event。
- `event` 图上只有少数几个 bin 有计数，是因为只有少数 event ID 产生了 LSO 记录。某个 event 如果在 LSO 中产生很多 step，它会贡献很多行，因此同一个 event ID 会在 histogram 中被重复计数，形成较高的柱。
- ROOT 默认 `Draw("event")` 会自动选择 histogram binning。横轴上看到的 `2600`、`2900` 等数字是 event ID 坐标或 bin 附近的刻度。要检查精确 event ID 和每个 event 的行数，需要用更细的 binning 或直接 scan tree。

常用 ROOT 检查命令：

```cpp
TFile* f = TFile::Open("output/spect_tc99m_iso.root");
TTree* t = (TTree*)f->Get("tree_chroma");
t->GetEntries();
t->Scan("event:hits:trackID:edep:xpos:ypos:zpos", "", "", 50);
t->Draw("event>>hEvent(10000,0,10000)");
```

其中 `t->GetEntries()` 返回 tree 的总行数；`Scan` 可以逐行查看 event 和 hit 记录；`Draw("event>>hEvent(10000,0,10000)")` 用更细的 event binning 画图，更容易看出哪些整数 event ID 真正出现过。

当前单位：

- 位置：`mm`
- 时间：`ns`
- 能量沉积：`keV`
- 粒子动能：`keV`
- 动量分量：`keV`

注意：`particle_name` 当前不是字符串，而是数值索引：

- `1`：gamma
- `2`：neutron
- `3`：electron
- `4`：positron
- `5`：other

## 如何判断运行成功

成功的 smoke test 应该在 log 中看到类似输出：

```text
Run Summary
  Number of events processed : 200
... write Root file : ../output/spect_tc99m_smoke.root - done
... close Root file : ../output/spect_tc99m_smoke.root - done
```

同时下面这个文件应该存在且非空：

```bash
/RHEL7/home/lwang2/g4spect_unit/output/spect_tc99m_smoke.root
```

最近一次检查时间：`2026-07-13 17:13 PDT`。当时 smoke test 已成功完成，并生成约 `728K` 的 ROOT 文件。

## 操作注意事项

- 每次修改几何、敏感探测器或输出格式后，先跑 `tc99m_beam_smoke.mac`。
- smoke test 通过后，再跑 `tc99m_point_iso.mac`。
- 各向同性点源命中少时，先检查准直器接受角，不要马上判断为 bug。
- 首选几何检查工具是 `geometry_exports/spect_geometry.wrl`，它由 Geant4 `VRML2FILE` 从当前 geometry 直接导出。
- `visualization/SPECT_geometry_3D.html` 只是辅助说明图，需要和 `src/SpectDetectorConstruction.cc` 保持一致，但不能替代 Geant4 导出的几何文件。
- 当前服务器出现过不明原因重启。在原因查清之前，不建议运行大规模事件数、完整重建或新的 GDML/Geant4 大型构建。
