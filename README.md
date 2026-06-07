# 🏙️ CS2 Modding Suite for Blender

A complete, all-in-one Blender add-on designed to heavily automate the asset pipeline for **Cities: Skylines II**.

Gone are the days of manual exports, tedious UV adjustments for windows, and repetitive material baking. This suite provides a unified HUD in the 3D Viewport to handle mesh separation, procedural Windows UV mapping, and Automated Batch Baking for Atlas textures.

<p align="center">
    <img src="images/panel.jpg" alt="CS2 Modding Suite HUD" style="height: 400px"/>
</p>

## 🛠️ Key Features

* **Smart FBX Exporter:** Duplicates your mesh, centers the origin, scales it perfectly for CS2, and automatically separates it into multiple `.fbx` files. You can now choose to separate the mesh by **Vertex Groups** OR by **Material Slots**.
* **Procedural Windows UV Grid:** Automatically maps the UVs of your windows to a 5x5 grid based on the CS2 day/night cycle logic. You control the brightness range!
* **Automated Batch Baking:** A 1-click solution to bake your `_BaseColor`, `_Normal`, and `_MaskMap`. The script automatically swaps the material states, configures Cycles rendering settings (Diffuse/Normal), performs the bake, and resets everything safely.

## 📦 Requirements

* **Blender 4.1** or higher (relies on the new Menu Switch node logic).
* Vertex Groups or Material names must follow the [Official CS2 Modding Conventions](https://cs2.paradoxwikis.com/Asset_Pipeline:_Buildings) (e.g., `Win`, `Wim`, `Gls`, `Gra`, `Wat`).

---

## 🚀 Installation

1. Download the script (`.py` file) or clone the repository.
2. Open Blender and go to **Edit > Preferences > Add-ons**.
3. Click **Install...** and select the downloaded Python file.
4. Check the box to enable **CS2 Modding Suite**.
5. Press `N` in the 3D Viewport to open the Sidebar. You will find a new tab called **CS2 Suite**.

---

## 📖 How To Use The Addon

### Module 1: Export 3D Model (FBX)

<p align="center">
    <img src="images/export_panel.jpg" alt="CS2 Modding Suite HUD"/>
</p>

Even though the Cities: Skylines II editor is improving and asset importing will get easier, this automatic FBX exporting script remains incredibly useful for Blender artists.

This module prepares and exports your building modularly, exactly how the CS2 engine expects it. Originally written to work exclusively with Vertex Groups, the script can now also read and select faces based on their assigned materials. This provides a better visual representation of the in-game model and a smarter, more streamlined workflow.

⚠️ **KEEP IN MIND:** You must add at least one Vertex Group or Material named `Base`. This represents the main building mesh, excluding any submeshes.

Once your 3D model is prepared with the appropriate Vertex Groups or Materials, follow these steps to export:

1. **Select your main object** in Object Mode.
2. Choose your **Separate By** method:
<table>
  <tr>
    <td width="30%" align="center">
      <img src="images/vertex_group.jpg" alt="Vertex Groups Example" width="100%">
    </td>
    <td width="70%">
      <b>Vertex Groups (Legacy Method):</b> Ideal if you use a single material but have assigned polygons to groups like <code>Base</code>, <code>Gls</code>, <code>Win</code>.<br/>This is the original approach, kept in the suite to give 3D artists maximum freedom and flexibility in managing their models.
    </td>
  </tr>
  <tr>
    <td width="30%" align="center">
      <img src="images/materials.jpg" alt="Materials Example" width="100%">
    </td>
    <td width="70%">
      <b>Materials (New & Recommended Method):</b> Ideal if you prefer assigning different materials (named <code>Base</code>, <code>Gls</code>, etc.) directly to the faces.<br/>Not only does this make the model visually more intuitive and easier to navigate in the viewport, but it also <b>prevents geometry overlaps</b>. While a single face can accidentally belong to multiple Vertex Groups, it can only have <em>one</em> material assigned to it, guaranteeing perfectly clean and unique separations!
    </td>
  </tr>
</table>

3. *(Optional)* Check **Reset Origin (Bounds)** if you want the script to automatically snap the pivot point to the absolute bottom-center of the mesh.
4. Click **Export to FBX**. The separated `.fbx` files will be automatically generated in a new folder located right next to your saved `.blend` file.

<p align="center">
    <image src="images/export_result.jpg">
</p>

---

### Module 2: Bake Windows UV Map
Cities: Skylines II uses a specific 5x5 UV grid for windows to determine when lights turn on at night.

<p align="center">
    <image src="images/Assetcreation_Window_Illumination_Room_Map_Reference.png" style="height: 400px" alt="Cities Skylines 2 Windows UV Map Reference">
</p>

1. Ensure the glass faces of your windows are assigned to a Vertex Group or a Material named exactly **`Win`** and/or **`Wim`** (for blurred glass windows).
2. Select your object in Object Mode.
3. In the CS2 Suite panel, set your desired light range:
    * **Min Room (Brightest):** `0` means the lights are almost always on.
    * **Max Room (Darkest):** `24` means the lights rarely turn on.
4. Click **Generate UV Grid**. The script will automatically unwrap, scale, and randomize the UV islands of your windows across the CS2 light grid.

---

### Module 3: Bake Material Atlas (Batch Baking)
This module saves hours of manual rendering when packing modular kits into a single Atlas. 
The Atlas is extremely useful if you're creating a pack of different assets that share similar materials.

To create it easily, just add a **Plane** to the scene and subdivide it to form a grid (2x2, 4x4, 8x8, etc.).

Here's an example of a simple 2x2 plane for our atlas:

<p align="center">
    <image src="images/atlas_plane.jpg" style="height: 250px" alt="Atlas Plane">
</p>

**⚠️ CRITICAL SETUP BEFORE BAKING:**
Every material applied to the Atlas Plane needs to have three distinct `Image Texture` nodes. Make sure to create a blank texture for each of them.

<p align="center">
    <image src="images/texture_images.jpg" style="height: 250px" alt="Texture Images">
</p>

The texture size should be 1024x1024, 2048x2048, 4096x4096, or a square of your choice. Smaller textures hold less detail but have a lower GPU impact compared to 4K/8K textures.
The texture names must consist of the 3D model's name followed by the texture type.

For the `_MaskMap` automation to work, your material must use a Switch node to toggle between the Base Color and the pure RGB Control Mask.

* Add the Switch node (Menu Switch node) in your Shader Editor.
* Select it, press **`F2`**, and rename it exactly to: **`BAKE_SWITCH`**.
* The script expects State 0 (A) to be your BaseColor/Normal, and State 1 (B) to be your pure RGB Mask.

![Node Setup](images/node_setup.jpg)

The `RGB to BW` node has to be connected to the *Metallic* texture map of your material.

The `Invert Color` node must be connected to your *Roughness* texture map (Cities: Skylines II uses *Glossiness*, which is the exact inverse of *Roughness*).

**How to Bake:**
1. Create 3 empty images in the Blender Image Editor using the standard naming convention (e.g., `MyModel_BaseColor`, `MyModel_Normal`, `MyModel_MaskMap`).
2. In the CS2 Suite panel, type the **Prefix** exactly as you named the images (e.g., `MyModel`).
3. Select the Atlas Plane you want to bake.
4. Check the boxes for the specific maps you want to generate. This is especially useful for saving time if you only need to fix and rebake a single map!
5. Click **Run Batch Bake**. 
6. Sit back! The script will force all materials to State A, configure Cycles for pure Diffuse baking (disabling lights/shadows), bake the Color, switch to Normal baking, swap the materials to State B, bake the MaskMap, and finally reset your materials safely to their original state. Note that **the Blue channel is not used by Cities: Skylines II**; the script automatically transfers its data into the Alpha channel (which the game uses for glossiness). The data is kept in the Blue channel purely to let you easily visualize the result in Blender.
7. *Don't forget to save your generated images (`Alt + S`) in the Image Editor!*