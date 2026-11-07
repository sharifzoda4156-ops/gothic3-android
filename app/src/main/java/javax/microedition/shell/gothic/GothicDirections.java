package javax.microedition.shell.gothic;

/**
 * Eight-way numeric keypad direction mapping for the Gothic 3 MIDlet.
 * Android-free so the mapping is unit-testable on a plain JVM.
 */
public final class GothicDirections {
    private static final int[] OCTANTS = {'6', '3', '2', '1', '4', '7', '8', '9'};

    private GothicDirections() {
    }

    /**
     * @param dx horizontal displacement from the fixed joystick center
     * @param dy vertical displacement; screen-space down is positive
     * @param deadZone minimum movement radius before a key is activated
     * @return MIDP numeric key code or zero while at rest
     */
    public static int keyFor(float dx, float dy, float deadZone) {
        if (!Float.isFinite(dx) || !Float.isFinite(dy) || !Float.isFinite(deadZone)) {
            return 0;
        }
        float radius = Math.max(0, deadZone);
        if (dx * dx + dy * dy <= radius * radius) {
            return 0;
        }
        double clockwiseFromRight = Math.atan2(-dy, dx);
        int octant = (int) Math.floor((clockwiseFromRight + Math.PI / 8) /
                (Math.PI / 4));
        return OCTANTS[Math.floorMod(octant, OCTANTS.length)];
    }
}
