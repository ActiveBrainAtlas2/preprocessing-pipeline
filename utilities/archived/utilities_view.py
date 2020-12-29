import os, sys
import shutil
import subprocess
from collections import defaultdict
import vtk
import numpy as np
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtkIdTypeArray

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)

from utilities.imported_atlas_utilities import all_known_structures_sided, convert_to_surround_name, all_known_structures, \
    get_warped_volume_basename_v2, MESH_DIR, get_original_volume_basename_v2


def get_mesh_filepath_v2(brain_spec, structure=None, resolution=None, level=None):
    if 'stack_f' in brain_spec:  # warped
        basename = get_warped_volume_basename_v2(alignment_spec=brain_spec, structure=structure,
                                                             resolution=resolution)

        # i have no idea what these are
        return os.path.join(MESH_DIR, 'XXXX', basename, 'YYYYY' + '.stl')
    else:
        basename = get_original_volume_basename_v2(stack_spec=brain_spec)
        if structure is None:
            structure = brain_spec['structure']
        assert structure is not None, 'Must specify structure'

        if level is None:
            mesh_fp = os.path.join(MESH_DIR, '%(stack)s',
                                   '%(basename)s',
                                   '%(basename)s_%(struct)s.stl') % \
                      {'stack': brain_spec['name'], 'basename': basename, 'struct': structure}
        else:
            stack = brain_spec['name']
            mesh_fp = os.path.join(MESH_DIR, '%(stack)s',
                                   '%(basename)s',
                                   '%(basename)s_%(struct)s_l%(level).1f.stl') % \
                      {'stack': brain_spec['name'], 'basename': basename, 'struct': structure, 'level': level}

        return mesh_fp


def load_mesh_v2(brain_spec, structure=None, resolution=None, return_polydata_only=True, level=None):

    mesh_fp = get_mesh_filepath_v2(brain_spec=brain_spec, structure=structure, resolution=resolution, level=level)
    print('mesh fp', mesh_fp)
    mesh = load_mesh_stl(mesh_fp, return_polydata_only=return_polydata_only)
    if mesh is None:
        raise Exception('Mesh is empty: %s.' % structure)
    return mesh


def load_meshes_v2(brain_spec,
                   structures=None,
                   resolution=None,
                   sided=True,
                   return_polydata_only=True,
                   include_surround=False,
                   level=.5):
    """
    Args:
        levels (float or a list of float): levels to load
    """

    kwargs = locals()

    if structures is None:
        if sided:
            if include_surround:
                structures = all_known_structures_sided + [convert_to_surround_name(s, margin='200um') for s in all_known_structures_sided]
            else:
                structures = all_known_structures_sided
        else:
            structures = all_known_structures

    if isinstance(level, float) or level is None:
        meshes = {}
        for structure in structures:
            # try:
            meshes[structure] = load_mesh_v2(brain_spec=brain_spec,
                                                         structure=structure,
                                                         resolution=resolution,
                                                         return_polydata_only=return_polydata_only,
                                                         level=level)
        # except Exception as e:
        # sys.stderr.write('Error loading mesh for %s: %s\n' % (structure, e))
        return meshes

    else:
        meshes_all_levels_all_structures = defaultdict(dict)
        print('are where here')
        for structure in structures:
            # try:
            mesh = load_mesh_v2(brain_spec=brain_spec, structure=structure,
                                                                resolution=resolution,
                                                                return_polydata_only=return_polydata_only,
                                                                level=level)
            meshes_all_levels_all_structures[structure][level] = mesh
            # except Exception as e:
            # raise e
            # sys.stderr.write('Error loading mesh for %s: %s\n' % (structure, e))
        meshes_all_levels_all_structures.default_factory = None

        return meshes_all_levels_all_structures

def load_mesh_stl(fn, return_polydata_only=False):
    """
    Args:
        return_polydata_only (bool): If true, return polydata; if false (default), return (vertices, faces)
    """

    if not os.path.exists(fn):
        print('load_mesh_stl: File does not exist %s\n' % fn)
        return None

    reader = vtk.vtkSTLReader()
    reader.SetFileName(fn)
    reader.Update()

    polydata = reader.GetOutput()
    assert polydata is not None

    if return_polydata_only:
        return polydata

    vertices = vtk_to_numpy(polydata.GetPoints().GetData())
    a = vtk_to_numpy(polydata.GetPolys().GetData())
    faces = np.c_[a[1::4], a[2::4], a[3::4]]

    return vertices, faces



def actor_mesh(polydata, color=(1.,1.,1.), wireframe=False, wireframe_linewidth=None, opacity=1., origin=(0,0,0)):
    """
    Args:
        color (float array): rgb between 0 and 1.
        origin: the initial shift for the mesh.
    """

    if polydata.GetNumberOfPoints() == 0:
        return None

    if origin[0] == 0 and origin[1] == 0 and origin[2] == 0:
        polydata_shifted = polydata
    else:
        polydata_shifted = move_polydata(polydata, origin)
        # Note that move_polydata() discards scalar data stored in polydata.

    m = vtk.vtkPolyDataMapper()
    m.SetInputData(polydata_shifted)
    a = vtk.vtkActor()
    a.SetMapper(m)

    # IF USE LOOKUP TABLE

    # from vtk.util.colors import *
    # lut = vtk.vtkLookupTable()
    # lut.SetNumberOfColors(256)
    # lut.Build()
    # for i in range(0, 16):
    #     lut.SetTableValue(i*16, red[0], red[1], red[2], 1)
    #     lut.SetTableValue(i*16+1, green[0], green[1], green[2], 1)
    #     lut.SetTableValue(i*16+2, blue[0], blue[1], blue[2], 1)
    #     lut.SetTableValue(i*16+3, black[0], black[1], black[2], 1)
    # m.SetLookupTable(lut)

    # m.ScalarVisibilityOn()
    # m.ScalarVisibilityOff()
    # m.SetScalarModeToDefault()
    # m.SetColorModeToDefault()
    # m.InterpolateScalarsBeforeMappingOff()
    # m.UseLookupTableScalarRangeOff()
    # m.ImmediateModeRenderingOff()
    # m.SetScalarMaterialModeToDefault()
    # m.GlobalImmediateModeRenderingOff()

    if wireframe:
        a.GetProperty().SetRepresentationToWireframe()
        if wireframe_linewidth is not None:
            a.GetProperty().SetLineWidth(wireframe_linewidth)

    a.GetProperty().SetColor(color)
    a.GetProperty().SetOpacity(opacity)

    return a

def move_polydata(polydata, d):
    # !!! IMPORTANT!! Note that this operation discards all scalar data (for example heatmap) in the input polydata.
    vs, fs = polydata_to_mesh(polydata)
    return mesh_to_polydata(vs + d, fs)


def polydata_to_mesh(polydata):
    """
    Extract vertice and face data from a polydata object.

    Returns:
        (vertices, faces)
    """

    vertices = np.array([polydata.GetPoint(i) for i in range(polydata.GetNumberOfPoints())])

    try:
        face_data_arr = vtk_to_numpy(polydata.GetPolys().GetData())

        faces = np.c_[face_data_arr[1::4],
                      face_data_arr[2::4],
                      face_data_arr[3::4]]
    except:
        sys.stderr.write('polydata_to_mesh: No faces are loaded.\n')
        faces = []

    return vertices, faces


def mesh_to_polydata(vertices, faces, num_simplify_iter=0, smooth=False):
    """
    Args:
        vertices ((num_vertices, 3) arrays)
        faces ((num_faces, 3) arrays)
    """

    polydata = vtk.vtkPolyData()

    points = vtk.vtkPoints()

    # points_vtkArray = numpy_support.numpy_to_vtk(vertices.flat)
    # points.SetData(points_vtkArray)

    for pt_ind, (x,y,z) in enumerate(vertices):
        points.InsertPoint(pt_ind, x, y, z)


    if len(faces) > 0:

        cells = vtk.vtkCellArray()

        cell_arr = np.empty((len(faces)*4, ), np.int)
        cell_arr[::4] = 3
        cell_arr[1::4] = faces[:,0]
        cell_arr[2::4] = faces[:,1]
        cell_arr[3::4] = faces[:,2]
        cell_vtkArray = numpy_to_vtkIdTypeArray(cell_arr, deep=1)
        cells.SetCells(len(faces), cell_vtkArray)

    # sys.stderr.write('fill cell array: %.2f seconds\n' % (time.time() - t))

    polydata.SetPoints(points)

    if len(faces) > 0:
        polydata.SetPolys(cells)
        # polydata.SetVerts(cells)

    if len(faces) > 0:
        polydata = simplify_polydata(polydata, num_simplify_iter, smooth)
    else:
        print('mesh_to_polydata: No faces are provided, so skip simplification.\n')

    return polydata


def simplify_polydata(polydata, num_simplify_iter=0, smooth=False):
    for simplify_iter in range(num_simplify_iter):


        deci = vtk.vtkQuadricDecimation()
        deci.SetInputData(polydata)

        deci.SetTargetReduction(0.8)
        # 0.8 means each iteration causes the point number to drop to 20% the original

        deci.Update()

        polydata = deci.GetOutput()

        if smooth:

            smoother = vtk.vtkWindowedSincPolyDataFilter()
    #         smoother.NormalizeCoordinatesOn()
            smoother.SetPassBand(.1)
            smoother.SetNumberOfIterations(20)
            smoother.SetInputData(polydata)
            smoother.Update()

            polydata = smoother.GetOutput()

        n_pts = polydata.GetNumberOfPoints()

        if polydata.GetNumberOfPoints() < 200:
            break


    return polydata


def rescale_polydata(polydata, factor):
    v, f = polydata_to_mesh(polydata)
    return mesh_to_polydata(v * factor, f)



def actor_sphere(position=(0,0,0), radius=.5, color=(1., 1., 1.), opacity=1.):
    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetCenter(position[0], position[1], position[2])
    sphereSource.SetRadius(radius)

    #create a mapper
    sphereMapper = vtk.vtkPolyDataMapper()
    sphereMapper.SetInputConnection(sphereSource.GetOutputPort())

    #create an actor
    sphereActor = vtk.vtkActor()
    sphereActor.SetMapper(sphereMapper)
    sphereActor.GetProperty().SetColor(color)
    sphereActor.GetProperty().SetOpacity(opacity)

    return sphereActor



def launch_vtk(actors, init_angle='45', window_name=None, window_size=None,
            interactive=True, snapshot_fn=None, snapshot_magnification=1,
            axes=True, background_color=(0,0,0), axes_label_color=(1,1,1),
            animate=False, movie_fp=None, framerate=10,
              view_up=None, position=None, focal=None, distance=1, depth_peeling=True):
    """
    Press q to close render window.
    s to take snapshot.
    g to print current viewup/position/focal.
    """

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(background_color)

    renWin = vtk.vtkRenderWindow()
    renWin.SetSize(1200,1080)
    # renWin.SetFullScreen(1)
    renWin.AddRenderer(renderer)

    ##########################

    # cullers = ren.GetCullers()
    # cullers.InitTraversal()
    # culler = cullers.GetNextItem()
    # # culler.SetSortingStyleToBackToFront()
    # culler.SetSortingStyleToFrontToBack()

    ##########################################
    if depth_peeling:
        # Enable depth peeling
        # http://www.vtk.org/Wiki/VTK/Examples/Cxx/Visualization/CorrectlyRenderTranslucentGeometry

        # 1. Use a render window with alpha bits (as initial value is 0 (false)):
        renWin.SetAlphaBitPlanes(True)

        # 2. Force to not pick a framebuffer with a multisample buffer
        # (as initial value is 8):
        renWin.SetMultiSamples(0);

        # 3. Choose to use depth peeling (if supported) (initial value is 0 (false)):
        renderer.SetUseDepthPeeling(True);

        # 4. Set depth peeling parameters
        # - Set the maximum number of rendering passes (initial value is 4):
        maxNoOfPeels = 8
        renderer.SetMaximumNumberOfPeels(maxNoOfPeels);
        # - Set the occlusion ratio (initial value is 0.0, exact image):
        occlusionRatio = 0.0
        renderer.SetOcclusionRatio(occlusionRatio);

    ##########################################

    camera = vtk.vtkCamera()

    if view_up is not None and position is not None and focal is not None:
        camera.SetViewUp(view_up[0], view_up[1], view_up[2])
        camera.SetPosition(position[0], position[1], position[2])
        camera.SetFocalPoint(focal[0], focal[1], focal[2])

    elif init_angle == '15':

        # 30 degree
        camera.SetViewUp(0, -1, 0)
        camera.SetPosition(-20, -20, -20)
        camera.SetFocalPoint(1, 1, 1)

    elif init_angle == '30':

        # 30 degree
        camera.SetViewUp(0, -1, 0)
        camera.SetPosition(-10, -5, -5)
        camera.SetFocalPoint(1, 1, 1)

    elif init_angle == '45':

        # 45 degree
        camera.SetViewUp(0, -1, 0)
        camera.SetPosition(-20, -30, -10)
        camera.SetFocalPoint(1, 1, 1)

    elif init_angle == 'sagittal': # left to right

        camera.SetViewUp(0, -1, 0)
        camera.SetPosition(0, 0, -distance)
        camera.SetFocalPoint(0, 0, 1)

    elif init_angle == 'coronal' or init_angle == 'coronal_posteriorToAnterior' :
        # posterior to anterior

        # coronal
        camera.SetViewUp(1.1, 0, 0)
        camera.SetPosition(-distance, 0, 0)
        camera.SetFocalPoint(-1, 0, 0)

#     elif init_angle == 'coronal_anteriorToPosterior':

#         # coronal
#         camera.SetViewUp(0, -1, 0)
#         camera.SetPosition(-2, 0, 0)
#         camera.SetFocalPoint(-1, 0, 0)

    elif init_angle == 'horizontal_bottomUp':

        # horizontal
        camera.SetViewUp(0, 0, -1)
        camera.SetPosition(0, distance, 0)
        camera.SetFocalPoint(0, -1, 0)

    elif init_angle == 'horizontal_topDown':

        # horizontal
        camera.SetViewUp(0, 0, 1)
        camera.SetPosition(0, -distance, 0)
        camera.SetFocalPoint(0, 1, 0)
    else:
        raise Exception("init_angle %s is not recognized." % init_angle)

    renderer.SetActiveCamera(camera)
    renderer.ResetCamera()

    # This must be before renWin.render(), otherwise the animation is stuck.
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    my_int_style = MyInteractorStyle(iren=iren, renWin=renWin, snapshot_fn='/tmp/tmp.png', camera=camera)
    iren.SetInteractorStyle(my_int_style) # Have problem closing window if use this

    for actor in actors:
        if actor is not None:
            renderer.AddActor(actor)

    if window_name is not None:
        renWin.SetWindowName(window_name)

    if window_size is not None:
        renWin.SetSize(window_size)

    ##################

    if axes:
        axes = add_axes(iren, text_color=axes_label_color)

    if animate:
        # http://www.vtk.org/Wiki/VTK/Examples/Python/Animation
        iren.Initialize()

        # Sign up to receive TimerEvent from interactor
        cb = vtkRecordVideoTimerCallback(movie_fp=movie_fp, win=renWin, iren=iren, camera=camera, framerate=framerate)
        cb.actors = actors
        iren.AddObserver('TimerEvent', cb.execute)
        timerId = iren.CreateRepeatingTimer(1000); # This cannot be too fast because otherwise image export cannot catch up.

    ##################

    renWin.Render()
    renWin.Finalize()

    if interactive:
        # if not animate:
        #     iren.Initialize()
        iren.Start()
    else:
        iren.Start()
        take_screenshot(renWin, snapshot_fn, magnification=snapshot_magnification)

    del my_int_style.iren
    del my_int_style.renWin

    if animate:
        if hasattr(cb, 'iren'):
            del cb.iren
        if hasattr(cb, 'win'):
            del cb.win

    # In order for window to successfully close, MUST MAKE SURE NO REFERENCE
    # TO IREN AND WIN still remain.

class MyInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, iren=None, renWin=None, snapshot_fn=None, camera=None):
        self.iren = iren
        self.renWin = renWin
        self.snapshot_fn = snapshot_fn
        self.camera = camera

        self.AddObserver("KeyPressEvent",self.keyPressEvent)

    def keyPressEvent(self,obj,event):
        key = self.iren.GetKeySym()
        if key == 'g':
            print('viewup: %f, %f, %f\n' % self.camera.GetViewUp())
            print('focal point: %f, %f, %f\n' % self.camera.GetFocalPoint())
            print('position: %f, %f, %f\n' % self.camera.GetPosition())
        elif key == 'e':
            print('Quit.')
            self.renWin.Finalize()
            self.iren.TerminateApp()
        elif key == 's':
            take_screenshot(self.renWin, self.snapshot_fn, 1)
        # return



def take_screenshot(win, file_path, magnification=10):

    windowToImageFilter = vtk.vtkWindowToImageFilter()

    windowToImageFilter.SetInput(win);
    windowToImageFilter.SetMagnification(magnification);
    # output image will be `magnification` times the render window size
    windowToImageFilter.SetInputBufferTypeToRGBA();
    windowToImageFilter.ReadFrontBufferOff();
    windowToImageFilter.Update();

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(file_path);
    writer.SetInputConnection(windowToImageFilter.GetOutputPort());
    writer.Write();



class vtkRecordVideoTimerCallback():
    def __init__(self, win, iren, camera, movie_fp, framerate=10):
        self.timer_count = 0
        self.movie_fp = movie_fp
        self.framerate = framerate
        self.iren = iren
        self.win = win
        self.camera = camera

        self.start_tick = 5 # wait 5 second then start

        self.azimuth_stepsize = 5.
        self.elevation_stepsize = 5.
        self.azimuth_rotation_start_tick = self.start_tick
        self.azimith_rotation_end_tick = self.azimuth_rotation_start_tick + 360./self.azimuth_stepsize
        self.elevation_rotation_start_tick = self.azimith_rotation_end_tick
        self.elevation_rotation_end_tick = self.elevation_rotation_start_tick + 360./self.elevation_stepsize

        self.finish_tick = self.elevation_rotation_end_tick

        tmppath = '/tmp/brain/video'
        if os.path.exists(tmppath):
            shutil.rmtree(tmppath)
        os.makedirs('/tmp/brain/video')

    def execute(self,obj,event):

        # print self.timer_count
        # for actor in self.actors:
        #     actor.SetPosition(self.timer_count, self.timer_count,0)

        if self.timer_count >= self.start_tick:

            if self.timer_count >= self.azimuth_rotation_start_tick and self.timer_count < self.azimith_rotation_end_tick:
                self.camera.Azimuth(self.azimuth_stepsize)
            elif self.timer_count >= self.elevation_rotation_start_tick and self.timer_count < self.elevation_rotation_end_tick:
                self.camera.Elevation(self.elevation_stepsize)
                self.camera.OrthogonalizeViewUp() # This is important! http://vtk.1045678.n5.nabble.com/rotating-vtkCamera-td1232623.html
            # arr = take_screenshot_as_numpy(self.win, magnification=1)

        if self.movie_fp is not None:
            take_screenshot(self.win, '/tmp/brain_video/%03d.png' % self.timer_count, magnification=1)

            if self.timer_count == self.finish_tick:

                cmd = 'ffmpeg -framerate %(framerate)d -pattern_type glob -i "/tmp/brain_video/*.png" -c:v libx264 -vf "scale=-1:1080,format=yuv420p" %(output_fp)s' % \
                {'framerate': self.framerate, 'output_fp': self.movie_fp}
                subprocess.run(cmd, shell=True)

                self.win.Finalize()
                self.iren.TerminateApp()
                del self.iren, self.win
                return

        self.win.Render()
        self.timer_count += 1



def add_axes(iren, text_color=(1,1,1)):

    axes = vtk.vtkAxesActor()

    # put axes at origin
    transform = vtk.vtkTransform()
    transform.Translate(0.0, 0.0, 0.0);
    axes.SetUserTransform(transform)

    axes.GetXAxisCaptionActor2D().GetCaptionTextProperty().SetColor(text_color[0],text_color[1],text_color[2]);
    axes.GetYAxisCaptionActor2D().GetCaptionTextProperty().SetColor(text_color[0],text_color[1],text_color[2]);
    axes.GetZAxisCaptionActor2D().GetCaptionTextProperty().SetColor(text_color[0],text_color[1],text_color[2]);

    widget = vtk.vtkOrientationMarkerWidget()
    widget.SetOutlineColor( 0.9300, 0.5700, 0.1300 );
    widget.SetOrientationMarker( axes );
    widget.SetInteractor( iren );
    # widget.SetViewport( 0.0, 0.0, 0.2, 0.2 );
    widget.SetEnabled( 1 );
    widget.InteractiveOn();
    return widget
