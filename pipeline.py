import os
import kfp.dsl as dsl
from kfp.dsl import PipelineVolume

# To compile the pipeline:
#   dsl-compile --py pipeline.py --output pipeline.tar.gz

from constants import PROJECT_ROOT, WORKSPACE, CONDA_PYTHON_CMD

def git_clone_op(repo_url: str):
    image='alpine/git:latest'
    
    commands = [
        f"git clone {repo_url} {PROJECT_ROOT}",
        f"cd {PROJECT_ROOT}"]

    volume_op = dsl.VolumeOp(
        name='create pipeline volume',
        resource_name='pipeline-pvc',
        modes=["ReadWriteOnce"],
        size='3Gi'
    )

    op = dsl.ContainerOp(
        name='git clone',
        image=image,
        command=['sh'],
        arguments=['-c', ' && '.join(commands)],
        container_kwargs={'image_pull_policy': 'IfNotPresent'},
        pvolumes={WORKSPACE: volume_op.volume}
    )

    return op

def generate_data(image: str, pvolume: PipelineVolume):

    commands = [
        f'{CONDA_PYTHON_CMD} {PROJECT_ROOT}/gen_plates.py',
        f'{CONDA_PYTHON_CMD} {PROJECT_ROOT}/gen_plates.py -s {PROJECT_ROOT}/.valid -n 200'
    ]

    return dsl.ContainerOp(
        name='data generation',
        image=image,
        command=['sh'],
        arguments=['-c', ' && '.join(commands)],
        container_kwargs={'image_pull_policy': 'IfNotPresent'},
        pvolumes={"/workspace": pvolume}
    )

def train_op(image: str, pvolume: PipelineVolume):
    return dsl.ContainerOp(
        name='training',
        image=image,
        command=[CONDA_PYTHON_CMD, f'{PROJECT_ROOT}/main.py'],
        arguments=['-m', 'train'],
        container_kwargs={'image_pull_policy': 'IfNotPresent'},
        pvolumes={"/workspace": pvolume}
    )

@dsl.pipeline(
    name='License Plate Recognition Training Pipeline',
    description='License Plate Recognition Training Pipeline to be executed on KubeFlow.'
)
def training_pipeline(image: str='quangphammessi/tensorflow_lprnet',
                        repo_url: str='https://github.com/quangphammessi/tensorflow_lprnet_test',
                        data_dir: str='/workspace'):
    git_clone = git_clone_op(repo_url=repo_url)

    gen_date = generate_data(image=image, pvolume=git_clone.pvolume)

    train = train_op(image=image, pvolume=gen_date.pvolume)


if __name__ == '__main__':
    import kfp.compiler as compiler

    compiler.Compiler().compile(training_pipeline, __file__ + '.tar.gz')