package org.bukkit.material;
import java.util.ArrayList;
import java.util.List;
import org.bukkit.Material;

public class Step extends TexturedMaterial {
   private static final List<Material> textures = new ArrayList();

   public Step() {
      super(Material.STEP);
   }

   /** @deprecated */
   @Deprecated
   public Step(int type) {
      super(type);
   }

   public Step(Material type) {
      super(textures.contains(type) ? Material.STEP : type);
      if (textures.contains(type)) {
         this.setMaterial(type);
      }

   }

   /** @deprecated */
   @Deprecated
   public Step(int type, byte data) {
      super(type, data);
   }

   /** @deprecated */
   @Deprecated
   public Step(Material type, byte data) {
      super(type, data);
   }

   public List<Material> getTextures() {
      return textures;
   }

   public boolean isInverted() {
      return (this.getData() & 8) != 0;
   }

   public void setInverted(boolean inv) {
      int dat = this.getData() & 7;
      if (inv) {
         dat |= 8;
      }

      this.setData((byte)dat);
   }

   /** @deprecated */
   @Deprecated
   protected int getTextureIndex() {
      return this.getData() & 7;
   }

   /** @deprecated */
   @Deprecated
   protected void setTextureIndex(int idx) {
      this.setData((byte)(this.getData() & 8 | idx));
   }

   public Step clone() {
      return (Step)super.clone();
   }

   public String toString() {
      return super.toString() + (this.isInverted() ? "inverted" : "");
   }

   static {
      textures.add(Material.STONE);
      textures.add(Material.SANDSTONE);
      textures.add(Material.WOOD);
      textures.add(Material.COBBLESTONE);
      textures.add(Material.BRICK);
      textures.add(Material.SMOOTH_BRICK);
      textures.add(Material.NETHER_BRICK);
      textures.add(Material.QUARTZ_BLOCK);
   }
}
