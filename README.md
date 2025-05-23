# CS2-Exporter-for-Blender
A Blender add-on for exporting assets to Cities: Skylines II. It duplicates the selected mesh, recenters and scales it, separates by vertex groups, and exports each part as an FBX file, properly rotated and ready for use in the game.
This script for automates the separation and export of 3D models based on **Vertex Groups**, ensuring compatibility with **Cities: Skylines II**.

## 🛠 Features

- Takes the currently selected 3D model in Blender.
- Separates the object into multiple objects, one for each **Vertex Group**.
- Renames the objects according to the Vertex Group name.
- Exports each object as an individual `.fbx` file.
- Designed to work around FBX compatibility issues with **Cities: Skylines II**.
- Requires Vertex Group names to follow the naming conventions provided in the game's modding guide.

## 📦 Requirements

- **Blender 3.5** or higher.
- Script can be run directly in **Blender** or via **VSCode** using the *Blender Development* extension.

## 🚀 How to Use

1. Open your 3D project in Blender.
2. Install the script as an addon. 
3. Select the main object you want to export.
4. Make sure the Vertex Group names are valid according to the Cities: Skylines II modding guide (Win, Wim, Gls, Gra).
5. Run the script from the "CS2 Exporter" panel on the right side of the 3D View.
6. Exported `.fbx` files will appear in a folder inside the directory of your Blender project.
