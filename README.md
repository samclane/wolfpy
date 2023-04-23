# Raycasting Renderer in Pygame
This is a simple 3D raycasting renderer implemented in Python using the Pygame library. It demonstrates the use of raycasting to render a 3D scene in a 2D game environment. The renderer uses a basic Digital Differential Analyzer (DDA) algorithm for raycasting and supports basic keyboard inputs for navigation in the scene.

## Features
- Simple raycasting implementation for 3D rendering in 2D environment
- Navigation using arrow keys (Up, Down, Left, Right)
- Example map with basic objects

## Requirements
- Python 3.6 or higher
- Pygame library

## Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/raycasting-renderer.git
```
2. Install the required Python packages using pip:
```bash
pip install pygame
```

## Usage
1. Run the main script to start the renderer:
```bash
python src/engine.py
```
2. Use the arrow keys to navigate in the 3D environment:
- Up: Move forward
- Down: Move backward
- Left: Turn left
- Right: Turn right

3. Press Esc or close the window to exit the renderer.
Customization
You can customize the example map by modifying the map_data list in raycasting_renderer.py. Each number in the list represents a different type of object or wall. You can adjust the MAP_SIZE constant to change the size of the map.

## License
TODO

## Contributing
Feel free to fork the repository and submit pull requests with improvements or additional features. If you encounter any issues or have suggestions, please open an issue on GitHub.