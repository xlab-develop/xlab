from subprocess import Popen, PIPE, STDOUT
import copy
import json
import os



### Setup class

def setup(parser):
    return Setup(parser)

class Setup:
    def __init__(self, parser):
        parser.add_argument("--exp-dir", default=False, action="store_const", const=True)

        self.parser = parser
    
    def __enter__(self):
        args = self.parser.parse_args()
        self.args = dict(vars(args))

        for key in ['exp_dir']:
            if key in self.args:
                del self.args[key]

        if args.exp_dir:
            # TODO: Find experiment dir

            dir = "runs/sample_" + args.function

            os.makedirs(dir, exist_ok=True)
            path = os.path.join(dir, 'config.json')
            with open(path, 'w') as out_file:
                json.dump(self.args, out_file, indent=4)

            print(dir)

            exit(0)
    
        hash = cache_get_hash(self.args)
        if cache_exists(hash):
            self.dir = cache_get_id(hash)
        else:
            self.dir = cache_create_unique_id(hash)


    
    def __exit__(self):
        print(self.dir)



### Experiment class

class Experiment:
    def __init__(self, executable, req_args, command):
        self.executable = executable
        self.command = command
        
        tmp_args = copy.copy(req_args)
        tmp_args['executable'] = executable

        command = command.format(**tmp_args)
        command_parts = command.split(' ')
        command_parts.append("--exp-dir")

        exe = Popen(command_parts, stdout=PIPE, stderr=STDOUT)
        out, _ = exe.communicate()
        dir = out.decode("utf-8")[:-1]
        
        path = os.path.join(dir, 'config.json')
        with open(path, 'r') as in_file:
            self.args = json.load(in_file)

    def run(self, use_cached=True, wait=True):
        command = command.format(**self.args)
        command_parts = command.split(' ')
        if not use_cached:
            command_parts.append('--exp-force')
        if not wait:
            command_parts.append('--exp-no-wait')
        
        exe = Popen(command_parts, stdout=STDOUT, stderr=STDOUT)
        exe.run()

    def _run_exe(self):
        pass