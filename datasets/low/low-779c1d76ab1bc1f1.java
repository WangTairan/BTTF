package org.apache.ibatis.scripting;
import java.util.HashMap;
import java.util.Map;

public class LanguageDriverRegistry {
   private final Map<Class<?>, LanguageDriver> LANGUAGE_DRIVER_MAP = new HashMap();
   private Class<?> defaultDriverClass = null;

   public void register(Class<?> cls) {
      if (cls == null) {
         throw new IllegalArgumentException("null is not a valid Language Driver");
      } else {
         LanguageDriver driver = (LanguageDriver)this.LANGUAGE_DRIVER_MAP.get(cls);
         if (driver == null) {
            try {
               driver = (LanguageDriver)cls.newInstance();
               this.LANGUAGE_DRIVER_MAP.put(cls, driver);
            } catch (Exception var4) {
               throw new ScriptingException("Failed to load language driver for " + cls.getName(), var4);
            }
         }

      }
   }

   public void register(LanguageDriver instance) {
      if (instance == null) {
         throw new IllegalArgumentException("null is not a valid Language Driver");
      } else {
         LanguageDriver driver = (LanguageDriver)this.LANGUAGE_DRIVER_MAP.get(instance.getClass());
         if (driver == null) {
            this.LANGUAGE_DRIVER_MAP.put(instance.getClass(), driver);
         }

      }
   }

   public LanguageDriver getDriver(Class<?> cls) {
      return (LanguageDriver)this.LANGUAGE_DRIVER_MAP.get(cls);
   }

   public LanguageDriver getDefaultDriver() {
      return this.getDriver(this.getDefaultDriverClass());
   }

   public Class<?> getDefaultDriverClass() {
      return this.defaultDriverClass;
   }

   public void setDefaultDriverClass(Class<?> defaultDriverClass) {
      this.register(defaultDriverClass);
      this.defaultDriverClass = defaultDriverClass;
   }
}
