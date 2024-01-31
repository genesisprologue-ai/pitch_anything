
<script setup>
</script>
<template>
    <div class="w-full p-3">
        <Skeleton class="mb-2"></Skeleton>
        <Skeleton width="10rem" class="mb-2"></Skeleton>
        <Skeleton width="5rem" class="mb-2"></Skeleton>
        <Skeleton height="2rem" class="mb-2"></Skeleton>
        <Skeleton width="10rem" height="4rem"></Skeleton>
    </div>
</template>

<script>
import Skeleton from 'primevue/skeleton'

export default {
    components: {
        Skeleton
    }
}
</script>