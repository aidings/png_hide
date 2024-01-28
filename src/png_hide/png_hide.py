from PIL import Image
from loguru import logger
from io import BytesIO


class PNGHide:
    def __init__(self, hide_mode='endian') -> None:
        """hide str information into png image

        Args:
            hide_mode (str, optional): hide mode['lsb' in image, 'endian' to append image]. Defaults to 'endian'.
        """
        self.magic_bytes = {
            "unencryptedLSB": 0xdeadc0de,
            "unencrypted": 0x5afec0de
        }
        self.hide_mode = hide_mode

    @staticmethod 
    def __changeLast2Bits(origByte: int, newBits: int) -> int:
        """
        This function replaces the 2 LSBs of the given origByte with newBits
        """
        # First shift bits to left 2 times
        # Then shift bits to right 2 times, now we lost the last 2 bits
        # Perform OR operation between original_number and new_bits

        return (origByte >> 2) << 2 | newBits

    @staticmethod
    def __filesizeToBytes(data: bytes) -> bytes:
        """
        This function returns the size of data in 8 bytes
        """
        return (len(data)).to_bytes(8, byteorder='big')

    @staticmethod
    def __serializeData(data: bytes, padding: int = 1) -> list:
        """
        This function packs data into groups of 2bits and returns that list
        """
        serializedData = list()
        for datum in data:
            serializedData.append((datum >> 6) & 0b11)
            serializedData.append((datum >> 4) & 0b11)
            serializedData.append((datum >> 2) & 0b11)
            serializedData.append((datum >> 0) & 0b11)

        while len(serializedData) % padding != 0:
            serializedData.append(0)

        return serializedData

    @staticmethod
    def __deserializeData(data: list) -> bytes:
        """
        This function takes data and unpacks the '2bits groups' to get original data back
        """
        deserializeData = list()
        for i in range(0, len(data) - 4 + 1, 4):
            datum = (data[i] << 6) + (data[i + 1] << 4) + (data[i + 2] << 2) + (data[i + 3] << 0)
            deserializeData.append(datum)

        return bytes(deserializeData)

    def encode(self, inputImagePath: str, hide_strs: str, outputImagePath: str) -> None:
        """
        This function hides the fileToHidePath file inside the image located at inputImagePath,
        and saves this modified image to outputImagePath.
        """
        # fp = open(fileToHidePath, "rb")

        # data = fp.read()
        data = bytes(hide_strs, "utf-8")
        logger.debug("[*] {} file size : {} bytes".format(hide_strs, len(data)))

        if self.hide_mode == "lsb":
            if isinstance(inputImage, Image.Image):
                image = inputImage
            else:
                image = Image.open(inputImagePath).convert('RGB')
            pixels = image.load()

            data = (self.magic_bytes["unencryptedLSB"]).to_bytes(4, byteorder='big') + self.__filesizeToBytes(data) + data
            logger.debug("[*] Magic bytes used: {}".format(hex(self.magic_bytes["unencryptedLSB"])))

            if len(data) > (image.size[0] * image.size[1] * 6) // 8:
                logger.warning("[*] Maximum hidden file size exceeded")
                logger.warning("[*] Maximum hidden file size for this image: {}".format((image.size[0] * image.size[1] * 6) // 8))
                logger.warning("[~] To hide this file, choose a bigger resolution")
                exit()

            logger.debug("[*] Hiding file in image")
            data = self.__serializeData(data, padding=3)
            data.reverse()

            imageX, imageY = 0, 0
            while data:
                # Pixel at index x and y
                pixel_val = pixels[imageX, imageY]

                # Hiding data in all 3 channels of each Pixel
                pixel_val = (self.__changeLast2Bits(pixel_val[0], data.pop()),
                            self.__changeLast2Bits(pixel_val[1], data.pop()),
                            self.__changeLast2Bits(pixel_val[2], data.pop()))

                # Save pixel changes to Image
                pixels[imageX, imageY] = pixel_val

                if imageX == image.size[0] - 1:          # If reached the end of X Axis
                    # Increment on Y Axis and reset X Axis
                    imageX = 0
                    imageY += 1
                else:
                    # Increment on X Axis
                    imageX += 1

            if not outputImagePath:
                outputImagePath = ".".join(inputImagePath.split(".")[:-1]) + "_with_hidden_file" + "." + inputImagePath.split(".")[-1]

            logger.debug(f"[+] Saving image to {outputImagePath}")
            image.save(outputImagePath)
        elif self.hide_mode == "endian":
            logger.warning("[!] Warning: You should encrypt file if using endian mode")
            data = data + self.__filesizeToBytes(data) + (self.magic_bytes["unencrypted"]).to_bytes(4, byteorder='little')
            logger.debug("[*] Magic bytes used: {}".format(hex(self.magic_bytes["unencrypted"])))

            # inputImage = open(inputImagePath, "rb").read()
            if isinstance(inputImagePath, Image.Image):
                image = inputImagePath
            else:
                image = Image.open(inputImagePath).convert('RGB')
            bytesIO = BytesIO()
            image.save(bytesIO, format='PNG')
            inputImage = bytesIO.getvalue()
            
            inputImage += data

            outputImage = open(outputImagePath, "wb")
            outputImage.write(inputImage)
            outputImage.close()
        else:
            raise "Invalid hide mode"
    
    def decode(self, inputImagePath: str) -> None:
        """
        This function extracts the hidden file from inputImagePath image and saves it to outputFilePath
        """

        inputImage = open(inputImagePath, "rb").read()
        if int.from_bytes(inputImage[-4:], byteorder='little') in [self.magic_bytes["unencrypted"]]:
            logger.debug("[+] Hidden file found in image")
            hiddenDataSize = int.from_bytes(inputImage[-12:-4], byteorder="big")
            hiddenData = inputImage[-hiddenDataSize - 12:-12]

            return hiddenData.decode()
        else:

            image = Image.open(inputImagePath).convert('RGB')
            pixels = image.load()

            data = list()                                 # List where we will store the extracted bits
            for imageY in range(image.size[1]):
                for imageX in range(image.size[0]):
                    if len(data) >= 48:
                        break

                    # Read pixel values traversing from [0, 0] to the end
                    pixel = pixels[imageX, imageY]

                    # Extract hidden message in chunk of 2 bits from each Channel
                    data.append(pixel[0] & 0b11)
                    data.append(pixel[1] & 0b11)
                    data.append(pixel[2] & 0b11)

            if self.__deserializeData(data)[:4] == bytes.fromhex(hex(self.magic_bytes["unencryptedLSB"])[2:]):
                logger.debug("[+] Hidden file found in image")
            else:
                logger.warning("[!] Image don't have any hidden file")
                logger.warning("[*] Magic bytes found:    0x{}".format(self.__deserializeData(data)[:4].hex()))
                logger.warning("[*] Magic bytes supported: {}".format(", ".join([hex(x) for x in self.magic_bytes.values()])))
                exit()

            logger.debug("[*] Extracting hidden file from image")
            hiddenDataSize = int.from_bytes(self.__deserializeData(data)[4:16], byteorder='big') * 4

            data = list()
            for imageY in range(image.size[1]):
                for imageX in range(image.size[0]):
                    if len(data) >= hiddenDataSize + 48:
                        break

                    # Read pixel values traversing from [0, 0] to the end
                    pixel = pixels[imageX, imageY]

                    # Extract hidden message in chunk of 2 bits from each Channel
                    data.append(pixel[0] & 0b11)
                    data.append(pixel[1] & 0b11)
                    data.append(pixel[2] & 0b11)

            data = self.__deserializeData(data[48:])

            return data.decode()