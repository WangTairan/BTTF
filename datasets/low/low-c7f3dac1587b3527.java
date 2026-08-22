package org.apache.ibatis.io;
import java.io.InputStream;
import java.net.URL;

public class ClassLoaderWrapper {
    ClassLoader defaultClassLoader;
    ClassLoader systemClassLoader;

    ClassLoaderWrapper() {
        try {
            this.systemClassLoader = ClassLoader.getSystemClassLoader();
        }
        catch (SecurityException securityException) {
            // empty catch block
        }
    }

    public URL getResourceAsURL(String resource) {
        return this.getResourceAsURL(resource, this.getClassLoaders(null));
    }

    public URL getResourceAsURL(String resource, ClassLoader classLoader) {
        return this.getResourceAsURL(resource, this.getClassLoaders(classLoader));
    }

    public InputStream getResourceAsStream(String resource) {
        return this.getResourceAsStream(resource, this.getClassLoaders(null));
    }

    public InputStream getResourceAsStream(String resource, ClassLoader classLoader) {
        return this.getResourceAsStream(resource, this.getClassLoaders(classLoader));
    }

    public Class<?> classForName(String name) throws ClassNotFoundException {
        return this.classForName(name, this.getClassLoaders(null));
    }

    public Class<?> classForName(String name, ClassLoader classLoader) throws ClassNotFoundException {
        return this.classForName(name, this.getClassLoaders(classLoader));
    }

    InputStream getResourceAsStream(String resource, ClassLoader[] classLoader) {
        for (ClassLoader cl : classLoader) {
            if (null == cl) continue;
            InputStream returnValue = cl.getResourceAsStream(resource);
            if (null == returnValue) {
                returnValue = cl.getResourceAsStream("/" + resource);
            }
            if (null == returnValue) continue;
            return returnValue;
        }
        return null;
    }

    URL getResourceAsURL(String resource, ClassLoader[] classLoader) {
        for (ClassLoader cl : classLoader) {
            if (null == cl) continue;
            URL url = cl.getResource(resource);
            if (null == url) {
                url = cl.getResource("/" + resource);
            }
            if (null == url) continue;
            return url;
        }
        return null;
    }

    Class<?> classForName(String name, ClassLoader[] classLoader) throws ClassNotFoundException {
        for (ClassLoader cl : classLoader) {
            if (null == cl) continue;
            try {
                Class<?> c = Class.forName(name, true, cl);
                if (null == c) continue;
                return c;
            }
            catch (ClassNotFoundException classNotFoundException) {
                // empty catch block
            }
        }
        throw new ClassNotFoundException("Cannot find class: " + name);
    }

    ClassLoader[] getClassLoaders(ClassLoader classLoader) {
        return new ClassLoader[]{classLoader, this.defaultClassLoader, Thread.currentThread().getContextClassLoader(), this.getClass().getClassLoader(), this.systemClassLoader};
    }
}
