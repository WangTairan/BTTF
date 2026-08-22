package org.bukkit.material;
import org.bukkit.Material;

/* loaded from: Cauldron.class */
public class Cauldron extends MaterialData {
    private static final int CAULDRON_FULL = 3;
    private static final int CAULDRON_EMPTY = 0;

    public Cauldron() {
        super(Material.CAULDRON);
    }

    @Deprecated
    public Cauldron(int type, byte data) {
        super(type, data);
    }

    @Deprecated
    public Cauldron(byte data) {
        super(Material.CAULDRON, data);
    }

    public boolean isFull() {
        return getData() >= CAULDRON_FULL;
    }

    public boolean isEmpty() {
        return getData() <= 0;
    }

    @Override // org.bukkit.material.MaterialData
    public String toString() {
        return (isEmpty() ? "EMPTY" : isFull() ? "FULL" : ((int) getData()) + "/3 FULL") + " CAULDRON";
    }

    @Override // org.bukkit.material.MaterialData
    public Cauldron clone() {
        return (Cauldron) super.m254clone();
    }
}
