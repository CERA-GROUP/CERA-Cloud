# BSD Licensed, Copyright (c) 2006-2008 MetaCarta, Inc.

from CeraCache.Cache import Cache
import sys, os, time, warnings, tempfile

class Disk (Cache):
    def __init__ (self, base = None, umask = '002', **kwargs):
        Cache.__init__(self, **kwargs)
        self.basedir = base
        self.umask = int(umask, 0)
        if sys.platform.startswith("java"):
            from java.io import File
            self.file_module = File
            self.platform = "jython"
        else:
            self.platform = "cpython"

        if not self.access(base, 'read'):
            self.makedirs(base)

    def makedirs(self, path, hide_dir_exists=True):
        if hasattr(os, "umask"):
            old_umask = os.umask(self.umask)
        try:
            os.makedirs(path)
        except OSError, E:
            # os.makedirs can suffer a race condition because it doesn't check
            # that the directory  doesn't exist at each step, nor does it
            # catch errors. This lets 'directory exists' errors pass through,
            # since they mean that as far as we're concerned, os.makedirs
            # has 'worked'
            if E.errno != 17 or not hide_dir_exists:
                raise E
        if hasattr(os, "umask"):
            os.umask(old_umask)

    def access(self, path, type='read'):
        try:
            if self.platform == "jython":
                if type == "read":
                    return self.file_module(path).canRead()
                else:
                    return self.file_module(path).canWrite()
            else:
                if type =="read":
                    return os.access(path, os.R_OK)
                else:
                    return os.access(path, os.W_OK)
        except Exception, E:
            return False

    def getKey (self, tile):
        filename = ""
        prefix = tile.layer.name
        if (len(tile.layer.cache_prefix) > 0):
            prefix = tile.layer.cache_prefix

        if (tile.x > 1000000 or tile.y > 1000000):
            components = ( self.basedir,
                            prefix,
                            "%02d" % tile.z,
                            "m%03d" % int(tile.x / 1000000),
                            "t%03d" % (int(tile.x / 1000) % 1000),
                            "%03d" % (int(tile.x) % 1000),
                            "m%03d" % int(tile.y / 1000000),
                            "t%03d" % (int(tile.y / 1000) % 1000),
                            "%03d.%s" % (int(tile.y) % 1000, tile.layer.extension)
                        )
        elif (tile.x > 1000 or tile.y > 1000):
            components = ( self.basedir,
                            prefix,
                            "%02d" % tile.z,
                            "t%03d" % (int(tile.x / 1000) % 1000),
                            "%03d" % (int(tile.x) % 1000),
                            "t%03d" % (int(tile.y / 1000) % 1000),
                            "%03d.%s" % (int(tile.y) % 1000, tile.layer.extension)
                        )
        else:
            components = ( self.basedir,
                            prefix,
                            "%02d" % tile.z,
                            "%03d" % int(tile.x),
                            "%03d.%s" % (int(tile.y), tile.layer.extension)
                        )
        filename = os.path.join( *components )
        return filename

    def get (self, tile):
        filename = self.getKey(tile)
        if self.access(filename, 'read'):
            if self.sendfile:
                return filename
            else:
                tile.data = file(filename, "rb").read()
                return tile.data
        else:
            return None

    def set (self, tile, data):
        if self.readonly: return data
        filename = self.getKey(tile)
        dirname  = os.path.dirname(filename)
        if not self.access(dirname, 'write'):
            self.makedirs(dirname)

#        if hasattr(os, "umask"):
#            old_umask = os.umask(self.umask)
#        tmpfile = filename + ".%d.tmp" % os.getpid()
#        output = file(tmpfile, "wb")
#        output.write(data)
#        output.close()
#        if hasattr(os, "umask"):
#            os.umask(old_umask);

        fh, tmpfile = tempfile.mkstemp('.tmp', 'cache_%d_' % os.getpid(), dirname)

        output = os.fdopen(fh, 'w')
        output.write(data)
        output.close();

        # if something goes wrong while renaming the tile we assume that
        # another thread is currently writing the tile, so we simply
        # ignore any problems and go on.
        try:
            os.rename(tmpfile, filename)
        except Exception:
            pass

        if os.path.exists(tmpfile):
            os.unlink(tmpfile)

        tile.data = data
        return data

    def delete (self, tile):
        filename = self.getKey(tile)
        if self.access(filename, 'read'):
            os.unlink(filename)

    def attemptLock (self, tile):
        name = self.getLockName(tile)
        try:
            self.makedirs(name, hide_dir_exists=False)
            return True
        except OSError:
            pass
        try:
            st = os.stat(name)
            if st.st_ctime + self.stale < time.time():
                warnings.warn("removing stale lock %s" % name)
                # remove stale lock
                self.unlock(tile)
                self.makedirs(name)
                return True
        except OSError:
            pass
        return False

    def unlock (self, tile):
        name = self.getLockName(tile)
        try:
            os.rmdir(name)
        except OSError, E:
            print >>sys.stderr, "unlock %s failed: %s" % (name, str(E))
