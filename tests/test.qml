import QtQuick
import QtQuick3D
import "."

View3D {
    id: view
    anchors.fill: parent
    environment: SceneEnvironment {
        clearColor: "transparent"
        backgroundMode: SceneEnvironment.Color
        antialiasingMode: SceneEnvironment.HighQuality
    }

    Node {
        id: sceneRoot

        // Загружаем твой файл MyCude.qml как компонент
        MyCube {
            id: fallingBody
            objectName: "fallingBody" // Оставляем это имя для Python

            // Если кубик в MyCude.qml слишком мелкий, подкрути масштаб тут
            scale: Qt.vector3d(100, 100, 100)
        }
    }

    DirectionalLight { eulerRotation.x: -30; brightness: 2.0 }
    PointLight { position: Qt.vector3d(0, 500, 500); brightness: 1.5 }

    PerspectiveCamera {
        id: camera
        position: Qt.vector3d(0, 0, 1000)
        clipNear: 0.1
        clipFar: 5000
    }
}