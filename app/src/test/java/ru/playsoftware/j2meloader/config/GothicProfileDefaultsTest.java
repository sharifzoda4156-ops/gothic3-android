package ru.playsoftware.j2meloader.config;

import org.junit.Test;
import static org.junit.Assert.*;

public class GothicProfileDefaultsTest {
    @Test
    public void creates480x640PortraitDefaults() {
        ProfileModel profile = new ProfileModel();
        GothicProfileDefaults.applyPreset(profile);

        assertEquals(ProfileModel.VERSION, profile.version);
        assertEquals(480, profile.screenWidth);
        assertEquals(640, profile.screenHeight);
        assertEquals(2, profile.orientation);
        assertEquals(1, profile.screenScaleType);
        assertEquals(1, profile.screenGravity);
        assertEquals(100, profile.screenScaleRatio);
        assertTrue(profile.screenKeepAspectRatio);
        assertFalse(profile.screenFilter);
        assertTrue(profile.forceFullscreen);
        assertFalse(profile.showKeyboard);
        assertEquals(3, profile.vkType);
        assertTrue(profile.touchInput);
        assertEquals(0, profile.fpsLimit);
        assertEquals(1, profile.graphicsMode);
    }

    @Test
    public void migrationRecognizesOnlyUnchangedLegacyResolution() {
        ProfileModel legacy = new ProfileModel();
        legacy.screenWidth = 240;
        legacy.screenHeight = 320;
        assertTrue(GothicProfileDefaults.isLegacyDefaultResolution(legacy));

        legacy.screenWidth = 480;
        legacy.screenHeight = 640;
        assertFalse(GothicProfileDefaults.isLegacyDefaultResolution(legacy));
    }
}
