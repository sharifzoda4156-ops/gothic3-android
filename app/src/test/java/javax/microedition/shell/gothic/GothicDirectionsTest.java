package javax.microedition.shell.gothic;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class GothicDirectionsTest {
    @Test
    public void mapsEightDirectionsToOriginalNumberPad() {
        assertEquals('6', GothicDirections.keyFor(10, 0, 2));
        assertEquals('3', GothicDirections.keyFor(10, -10, 2));
        assertEquals('2', GothicDirections.keyFor(0, -10, 2));
        assertEquals('1', GothicDirections.keyFor(-10, -10, 2));
        assertEquals('4', GothicDirections.keyFor(-10, 0, 2));
        assertEquals('7', GothicDirections.keyFor(-10, 10, 2));
        assertEquals('8', GothicDirections.keyFor(0, 10, 2));
        assertEquals('9', GothicDirections.keyFor(10, 10, 2));
    }

    @Test
    public void deadZoneHasNoInputAndIsRadial() {
        assertEquals(0, GothicDirections.keyFor(0, 0, 20));
        assertEquals(0, GothicDirections.keyFor(12, 12, 20));
        assertEquals(0, GothicDirections.keyFor(20, 0, 20));
        assertEquals('6', GothicDirections.keyFor(21, 0, 20));
        assertEquals(0, GothicDirections.keyFor(Float.NaN, 0, 10));
    }

    @Test
    public void diagonalSectorsDoNotJitterNearCardinalAxis() {
        assertEquals('6', GothicDirections.keyFor(100, -20, 10));
        assertEquals('3', GothicDirections.keyFor(100, -50, 10));
        assertEquals('2', GothicDirections.keyFor(20, -100, 10));
        assertEquals('7', GothicDirections.keyFor(-100, 50, 10));
    }
}
