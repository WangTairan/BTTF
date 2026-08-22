package org.bukkit.configuration.serialization;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.apache.commons.lang.Validate;
import org.bukkit.Color;
import org.bukkit.FireworkEffect;
import org.bukkit.inventory.ItemStack;
import org.bukkit.potion.PotionEffect;
import org.bukkit.util.BlockVector;
import org.bukkit.util.Vector;

/* loaded from: ConfigurationSerialization.class */
public class ConfigurationSerialization {
    public static final String SERIALIZED_TYPE_KEY = "==";
    private final Class<? extends ConfigurationSerializable> clazz;
    private static Map<String, Class<? extends ConfigurationSerializable>> aliases = new HashMap();

    static {
        registerClass(Vector.class);
        registerClass(BlockVector.class);
        registerClass(ItemStack.class);
        registerClass(Color.class);
        registerClass(PotionEffect.class);
        registerClass(FireworkEffect.class);
    }

    protected ConfigurationSerialization(Class<? extends ConfigurationSerializable> clazz) {
        this.clazz = clazz;
    }

    protected Method getMethod(String name, boolean isStatic) {
        try {
            Method method = this.clazz.getDeclaredMethod(name, Map.class);
            if (!ConfigurationSerializable.class.isAssignableFrom(method.getReturnType())) {
                return null;
            }
            if (Modifier.isStatic(method.getModifiers()) != isStatic) {
                return null;
            }
            return method;
        } catch (NoSuchMethodException e) {
            return null;
        } catch (SecurityException e2) {
            return null;
        }
    }

    protected Constructor<? extends ConfigurationSerializable> getConstructor() {
        try {
            return this.clazz.getConstructor(Map.class);
        } catch (NoSuchMethodException e) {
            return null;
        } catch (SecurityException e2) {
            return null;
        }
    }

    protected ConfigurationSerializable deserializeViaMethod(Method method, Map<String, ?> args) {
        try {
            ConfigurationSerializable result = (ConfigurationSerializable) method.invoke(null, args);
            if (result == null) {
                Logger.getLogger(ConfigurationSerialization.class.getName()).log(Level.SEVERE, "Could not call method '" + method.toString() + "' of " + this.clazz + " for deserialization: method returned null");
                return null;
            }
            return result;
        } catch (Throwable ex) {
            Logger.getLogger(ConfigurationSerialization.class.getName()).log(Level.SEVERE, "Could not call method '" + method.toString() + "' of " + this.clazz + " for deserialization", ex instanceof InvocationTargetException ? ex.getCause() : ex);
            return null;
        }
    }

    protected ConfigurationSerializable deserializeViaCtor(Constructor<? extends ConfigurationSerializable> ctor, Map<String, ?> args) {
        try {
            return ctor.newInstance(args);
        } catch (Throwable ex) {
            Logger.getLogger(ConfigurationSerialization.class.getName()).log(Level.SEVERE, "Could not call constructor '" + ctor.toString() + "' of " + this.clazz + " for deserialization", ex instanceof InvocationTargetException ? ex.getCause() : ex);
            return null;
        }
    }

    public ConfigurationSerializable deserialize(Map<String, ?> args) {
        Constructor<? extends ConfigurationSerializable> constructor;
        Method method;
        Method method2;
        Validate.notNull(args, "Args must not be null");
        ConfigurationSerializable result = null;
        if (0 == 0 && (method2 = getMethod("deserialize", true)) != null) {
            result = deserializeViaMethod(method2, args);
        }
        if (result == null && (method = getMethod("valueOf", true)) != null) {
            result = deserializeViaMethod(method, args);
        }
        if (result == null && (constructor = getConstructor()) != null) {
            result = deserializeViaCtor(constructor, args);
        }
        return result;
    }

    public static ConfigurationSerializable deserializeObject(Map<String, ?> args, Class<? extends ConfigurationSerializable> clazz) {
        return new ConfigurationSerialization(clazz).deserialize(args);
    }

    public static ConfigurationSerializable deserializeObject(Map<String, ?> args) {
        if (args.containsKey(SERIALIZED_TYPE_KEY)) {
            try {
                String alias = (String) args.get(SERIALIZED_TYPE_KEY);
                if (alias == null) {
                    throw new IllegalArgumentException("Cannot have null alias");
                }
                Class<? extends ConfigurationSerializable> clazz = getClassByAlias(alias);
                if (clazz == null) {
                    throw new IllegalArgumentException("Specified class does not exist ('" + alias + "')");
                }
                return new ConfigurationSerialization(clazz).deserialize(args);
            } catch (ClassCastException ex) {
                ex.fillInStackTrace();
                throw ex;
            }
        }
        throw new IllegalArgumentException("Args doesn't contain type key ('==')");
    }

    public static void registerClass(Class<? extends ConfigurationSerializable> clazz) {
        DelegateDeserialization delegate = (DelegateDeserialization) clazz.getAnnotation(DelegateDeserialization.class);
        if (delegate == null) {
            registerClass(clazz, getAlias(clazz));
            registerClass(clazz, clazz.getName());
        }
    }

    public static void registerClass(Class<? extends ConfigurationSerializable> clazz, String alias) {
        aliases.put(alias, clazz);
    }

    public static void unregisterClass(String alias) {
        aliases.remove(alias);
    }

    public static void unregisterClass(Class<? extends ConfigurationSerializable> clazz) {
        do {
        } while (aliases.values().remove(clazz));
    }

    public static Class<? extends ConfigurationSerializable> getClassByAlias(String alias) {
        return aliases.get(alias);
    }

    public static String getAlias(Class<? extends ConfigurationSerializable> clazz) {
        SerializableAs alias;
        DelegateDeserialization delegate = (DelegateDeserialization) clazz.getAnnotation(DelegateDeserialization.class);
        if (delegate != null) {
            if (delegate.value() == null || delegate.value() == clazz) {
                delegate = null;
            } else {
                return getAlias(delegate.value());
            }
        }
        if (delegate == null && (alias = (SerializableAs) clazz.getAnnotation(SerializableAs.class)) != null && alias.value() != null) {
            return alias.value();
        }
        return clazz.getName();
    }
}
