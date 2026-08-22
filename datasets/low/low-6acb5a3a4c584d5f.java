package org.bukkit.command.defaults;
import com.google.common.collect.ImmutableList;
import java.util.List;
import org.apache.commons.lang.Validate;
import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;

/* loaded from: SetWorldSpawnCommand.class */
public class SetWorldSpawnCommand extends VanillaCommand {
    public SetWorldSpawnCommand() {
        super("setworldspawn");
        this.description = "Sets a worlds's spawn point. If no coordinates are specified, the player's coordinates will be used.";
        this.usageMessage = "/setworldspawn OR /setworldspawn <x> <y> <z>";
        setPermission("bukkit.command.setworldspawn");
    }

    @Override // org.bukkit.command.Command
    public boolean execute(CommandSender sender, String currentAlias, String[] args) {
        World world;
        int x;
        int y;
        int z;
        if (testPermission(sender)) {
            Player player = null;
            if (sender instanceof Player) {
                player = (Player) sender;
                world = player.getWorld();
            } else {
                world = Bukkit.getWorlds().get(0);
            }
            if (args.length == 0) {
                if (player == null) {
                    sender.sendMessage("You can only perform this command as a player");
                    return true;
                }
                Location location = player.getLocation();
                x = location.getBlockX();
                y = location.getBlockY();
                z = location.getBlockZ();
            } else if (args.length == 3) {
                try {
                    x = getInteger(sender, args[0], -30000000, 30000000, true);
                    y = getInteger(sender, args[1], 0, world.getMaxHeight(), true);
                    z = getInteger(sender, args[2], -30000000, 30000000, true);
                } catch (NumberFormatException ex) {
                    sender.sendMessage(ex.getMessage());
                    return true;
                }
            } else {
                sender.sendMessage(ChatColor.RED + "Usage: " + this.usageMessage);
                return false;
            }
            world.setSpawnLocation(x, y, z);
            Command.broadcastCommandMessage(sender, "Set world " + world.getName() + "'s spawnpoint to (" + x + ", " + y + ", " + z + ")");
            return true;
        }
        return true;
    }

    @Override // org.bukkit.command.Command
    public List<String> tabComplete(CommandSender sender, String alias, String[] args) {
        Validate.notNull(sender, "Sender cannot be null");
        Validate.notNull(args, "Arguments cannot be null");
        Validate.notNull(alias, "Alias cannot be null");
        return ImmutableList.of();
    }
}
