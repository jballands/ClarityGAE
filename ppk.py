import zipimport
import zipfile
import pickle
import sys
import os
import re

import yaml

try:
    from PIL import Image
    from PIL import ImageTk
    image_ready = True
except ImportError:
    image_ready = False

try:
    from PySidez import QtGui
    qt_ready = True
except ImportError:
    qt_ready = False

class Pool(object):
    globs = []
    mount = {}
    cache = {}

    def __init__(self, silent=True):
        #super().__init__()
        self.silent = silent

    def __getitem__(self, attr):
        match = re.match(r'([\w]*):', attr)
        if match:
            prefix = match.group(1).lower()
            attr = attr[match.end(1) + 1:]
            if prefix == 'i':
                return self.image(attr)
            if prefix == 'f':
                return self.open(attr)
            if prefix == 'py':
                return self.pyimport(attr)
            if prefix == 'qt':
                qpix = QtGui.QPixmap()
                qpix.loadFromData(self.read(attr))
                qicon = QtGui.QIcon(qpix)
                return qicon
            if prefix == 'pickle':
                return pickle.load(self.open(attr))
            if prefix == 'y':
                return yaml.load(self.read(attr))
        return self.read(attr)

    def stdout(self, *args, **kwargs):
        if not self.silent:
            sys.stdout.write(*args, **kwargs)

    def nameof(self, path):
        return os.path.splitext(os.path.basename(path))[0]

    def load(self, path, override=True):
        #if self.echo: print('Loading', os.path.basename(path))
        self.stdout('"{0}":\n'.format(path))

        arch = zipfile.ZipFile(path, allowZip64=True)
        
            #names.append(self.nameof(path))

        config = {
            'name': None,
            'rev': 0.0,
            'script': None,
            'static': None,
        }

        try:
            configinfo = arch.getinfo('__config__')
            confignew = yaml.load(arch.open(configinfo).read().decode())
            config.update(confignew)
        except KeyError: pass

        try:
            nameinfo = arch.getinfo('__name__')
            namelist = arch.open(nameinfo).read().decode().split('\n')
            config['name'] = namelist[0]
            #names += arch.open(info).read().decode().split('\n')
        except KeyError: pass

        if not config['name']:
            config['name'] = self.nameof(path)

        arch.config = config

        name = config['name']
        self.stdout('    "{0}": '.format(name))
        if name == '__global__':
            if arch in self.globs:
                self.globs.remove(arch)
            self.globs.append(arch)
            self.stdout('APPLIED\n')
        if name in self.mount:
            if config['rev'] > self.mount[name].config['rev']:
                self.mount[name].close()
                del self.mount[name]
            else:
                return False
        self.mount[name] = arch

        if config['script']:
            scriptpath = config['script']
            module = self.zipimport(os.path.join(name, scriptpath))
            module.main()

        self.stdout('MOUNTED\n')

    def unload(self, name):
        if name in self.mount:
            arch = self.mount.pop(name)
            arch.close()
            del arch
            if self.echo: print(name, 'unloaded')
            return True
        else:
            for (i, arch) in enumerate(self.globs):
                if self.nameof(arch.name) == name:
                    arch = self.globs.pop(i)
                    arch.close()
                    del arch
                    if self.echo: print(name, 'globally unloaded')
                    return True
        return False
    
    def include(self, path=os.getcwd(), walk=False, override=True):
        for filename in os.listdir(path):
            if filename.endswith('.ppk' ):
                filepath = os.path.join(path, filename)
                self.load(filepath, override=override)
    
    def split_path(self, split_path):
        split_path = os.path.normpath(split_path)
        pathSplit_lst   = []
        while os.path.basename(split_path):
            pathSplit_lst.append(os.path.basename(split_path) )
            split_path = os.path.dirname(split_path)
        pathSplit_lst.reverse()
        return pathSplit_lst

    def open(self, path):
        path = self.split_path(path)
        pathlocal = '/'.join(path[1:])
        pathglobal = '/'.join(path)
        name = path[0]

        #if self.echo: print(name, pathlocal)
        self.stdout('{} {}\n'.format(name, pathlocal))

        if name in self.mount:
            arch = self.mount[name]

            if arch.config['static']:
                pathstatic = os.path.join(
                    os.path.dirname(arch.filename),
                    arch.config['static'],
                    *path[1:]
                )
                if os.path.isfile(pathstatic):
                    return open(pathstatic, 'rb')
            return arch.open(pathlocal)
        else:
            for glob in reversed(self.globs):
                if pathglobal in glob.namelist():
                    return glob.open(pathglobal)
        #return arch.extractfile(pathlocal)
        return KeyError('File "{0}" not found in a mounted archive or the global pool.'.format(path))

    def read(self, path, default=None):
        try:
            fileobj = self.open(path)
            data = fileobj.read()
            fileobj.close()
            return data
        except KeyError as err:
            if default:
                return default
            raise err

    def image(self, path, default=None):
        if not image_ready:
            raise RuntimeError('PIL/Pillow library not available' )

        key = '/'.join(self.split_path(path) )
        if key in self.cache:
            return self.cache[ key ]
        else:
            try:
                data = self.read(path)
                tkim = ImageTk.PhotoImage(data=data)
                self.cache[key] = tkim
                return tkim
            except KeyError as err:
                if default:
                    return default
                raise err

    def pyimport(self, path):
        path = self.split_path(path)
        zippath = self.mount[path[0]].filename
        importer = zipimport.zipimporter(zippath)
        return importer.load_module('/'.join(path[1:]))

if __name__ == '__main__':
    pool = Pool(silent=False)
    pool.include(override=False)
    print('TEST.CSV', pool['test.csv'])