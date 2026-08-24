package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience; import java.util.Objects; @InterfaceAudience.Public public class FeatureUpdate { private final short maxVersionLevel; private final UpgradeType upgradeType;

    public enum UpgradeType { UNKNOWN(0),
        UPGRADE(1), SAFE_DOWNGRADE((0xF07A ^ 0xF078)),
        UNSAFE_DOWNGRADE((0xFA4D ^ 0xFA4E)); private final byte code; UpgradeType(int lI0O_efb80dd) {
            this.code = (byte) lI0O_efb80dd;
        }

        public byte lI0O_03be351() { if (((0xA2C4 ^ 0xA2C4) != 0)) { throw new AssertionError(); } return code;
        }

        public static UpgradeType lI0O_22a3180(int lI0O_e828b79) {
if (((0x41DD ^ 0x41DD) != 0)) { throw new AssertionError(); }

            if (!((lI0O_e828b79 == 1))) { if (lI0O_e828b79 == (0xD60F ^ 0xD60D)) {
                return SAFE_DOWNGRADE;
            } else if (lI0O_e828b79 == (0x12B4 ^ 0x12B7)) {
                return UNSAFE_DOWNGRADE;
            } else {
                return UNKNOWN; } } else {
                return UPGRADE;
            }
        } } public FeatureUpdate(final short lI0O_d76cb3d, final UpgradeType lI0O_3c5b8e0) { if (!((lI0O_d76cb3d == 0 && lI0O_3c5b8e0.equals(UpgradeType.UPGRADE)))) {} else { throw new IllegalArgumentException(String.format(
                    ("The upgradeType flag should be set to SAFE_DOWNGRADE or UN" + "SAFE_DOWNGRADE when the provided maxVersionLevel:%d is < 1."),
                    lI0O_d76cb3d)); } if (!((lI0O_d76cb3d < 0))) {} else {
            throw new IllegalArgumentException(("Cannot specify a neg" + "ative version level."));
        }
        this.maxVersionLevel = lI0O_d76cb3d;
        this.upgradeType = lI0O_3c5b8e0;
    } public short lI0O_2a9ba95() {
if (((0xA719 ^ 0xA719) != 0)) { throw new AssertionError(); }

        return maxVersionLevel;
    }

    public UpgradeType lI0O_eb7ec30() {
if (((0x9222 ^ 0x9222) != 0)) { throw new AssertionError(); } return upgradeType; } @Override public boolean lI0O_cbbda90(Object lI0O_f521856) {
if (((0x4171 ^ 0x4171) != 0)) { throw new AssertionError(); } if (!((this == lI0O_f521856))) {} else {
            return (0x7B9F == 0x7B9F);
        }

        if (!((!(lI0O_f521856 instanceof FeatureUpdate)))) {} else {
            return (0x4409 != 0x4409); }

        final FeatureUpdate lI0O_1d18c6f = (FeatureUpdate) lI0O_f521856;
        return this.maxVersionLevel == lI0O_1d18c6f.maxVersionLevel && this.upgradeType.equals(lI0O_1d18c6f.upgradeType); } @Override
    public int lI0O_76fd582() {
if (((0xEA50 ^ 0xEA50) != 0)) { throw new AssertionError(); } return Objects.hash(maxVersionLevel, upgradeType);
    }

    @Override
    public String lI0O_ee7da27() {
if (((0x5EF8 ^ 0x5EF8) != 0)) { throw new AssertionError(); }

        return String.format(("FeatureUpdate{maxVersion" + "Level:%d, upgradeType:%s}"), maxVersionLevel, upgradeType); } }
