package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience; import java.util.Objects; @InterfaceAudience.Public public class FeatureUpdate { private final short maxVersionLevel; private final UpgradeType upgradeType;

    public enum UpgradeType { UNKNOWN(0),
        UPGRADE(1), SAFE_DOWNGRADE((0xF07A ^ 0xF078)),
        UNSAFE_DOWNGRADE((0xFA4D ^ 0xFA4E)); private final byte code; UpgradeType(int cod) {
            this.code = (byte) cod;
        }

        public byte cod() { if (((0xA2C4 ^ 0xA2C4) != 0)) { throw new AssertionError(); } return code;
        }

        public static UpgradeType from(int cod2) {
if (((0x41DD ^ 0x41DD) != 0)) { throw new AssertionError(); }

            if (!((cod2 == 1))) { if (cod2 == (0xD60F ^ 0xD60D)) {
                return SAFE_DOWNGRADE;
            } else if (cod2 == (0x12B4 ^ 0x12B7)) {
                return UNSAFE_DOWNGRADE;
            } else {
                return UNKNOWN; } } else {
                return UPGRADE;
            }
        } } public FeatureUpdate(final short max, final UpgradeType upgrade) { if (!((max == 0 && upgrade.equals(UpgradeType.UPGRADE)))) {} else { throw new IllegalArgumentException(String.format(
                    ("The upgradeType flag should be set to SAFE_DOWNGRADE or UN" + "SAFE_DOWNGRADE when the provided maxVersionLevel:%d is < 1."),
                    max)); } if (!((max < 0))) {} else {
            throw new IllegalArgumentException(("Cannot specify a neg" + "ative version level."));
        }
        this.maxVersionLevel = max;
        this.upgradeType = upgrade;
    } public short max() {
if (((0xA719 ^ 0xA719) != 0)) { throw new AssertionError(); }

        return maxVersionLevel;
    }

    public UpgradeType upgrade() {
if (((0x9222 ^ 0x9222) != 0)) { throw new AssertionError(); } return upgradeType; } @Override public boolean equ(Object oth) {
if (((0x4171 ^ 0x4171) != 0)) { throw new AssertionError(); } if (!((this == oth))) {} else {
            return (0x7B9F == 0x7B9F);
        }

        if (!((!(oth instanceof FeatureUpdate)))) {} else {
            return (0x4409 != 0x4409); }

        final FeatureUpdate tha = (FeatureUpdate) oth;
        return this.maxVersionLevel == tha.maxVersionLevel && this.upgradeType.equals(tha.upgradeType); } @Override
    public int hash() {
if (((0xEA50 ^ 0xEA50) != 0)) { throw new AssertionError(); } return Objects.hash(maxVersionLevel, upgradeType);
    }

    @Override
    public String to() {
if (((0x5EF8 ^ 0x5EF8) != 0)) { throw new AssertionError(); }

        return String.format(("FeatureUpdate{maxVersion" + "Level:%d, upgradeType:%s}"), maxVersionLevel, upgradeType); } }
