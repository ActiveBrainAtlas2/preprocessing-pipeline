from pathlib import Path
import SimpleITK as sitk 
def get_save_dir(fix_brain):
    save_dir = Path('../data/automatic-alignment') / fix_brain
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir

def save_affine_transform(affine_transform,fix_brain):
    save_dir = get_save_dir(fix_brain)
    affine_save_path = (save_dir / '1-affine.tfm').as_posix()
    sitk.WriteTransform(affine_transform, affine_save_path)

def save_demons_transform(demons_transform,fix_brain):
    save_dir = get_save_dir(fix_brain)
    demons_save_path = (save_dir / '1-demons.tfm').as_posix()
    sitk.WriteTransform(demons_transform, demons_save_path)
